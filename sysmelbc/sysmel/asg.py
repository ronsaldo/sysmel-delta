from abc import ABC, abstractmethod
from typing import Any

from .target import *
from .parsetree import *
import copy

class ASGNodeDerivation(ABC):
    @abstractmethod
    def getSourcePosition(self) -> SourcePosition:
        pass

class ASGNodeSourceCodeDerivation(ASGNodeDerivation):
    def __init__(self, sourcePosition: SourcePosition) -> None:
        super().__init__()
        self.sourcePosition = sourcePosition

    def getSourcePosition(self) -> SourcePosition:
        return self.sourcePosition

class ASGNodeExpansionDerivation(ASGNodeDerivation):
    def __init__(self, algorithm, sourceNode) -> None:
        super().__init__()
        self.algorithm = algorithm
        self.sourceNode = sourceNode
        self.sourcePosition = None

    def getSourcePosition(self) -> SourcePosition:
        if self.sourcePosition is None:
            self.sourcePosition = self.sourceNode.sourceDerivation.getSourcePosition()
        return self.sourcePosition

class ASGNodeUnificationDerivation(ASGNodeDerivation):
    def __init__(self, originalNode, unifiedNode) -> None:
        super().__init__()
        self.originalNode = originalNode
        self.unifiedNode = unifiedNode
        self.sourcePosition = None

    def getSourcePosition(self) -> SourcePosition:
        if self.sourcePosition is None:
            self.sourcePosition = self.originalNode.sourceDerivation.getSourcePosition()
        return self.sourcePosition

class ASGNodeSyntaxExpansionDerivation(ASGNodeExpansionDerivation):
    pass
    
class ASGNodeNoDerivation(ASGNodeDerivation):
    Singleton = None

    def getSourcePosition(self) -> SourcePosition:
        return EmptySourcePosition.getSingleton()

    @classmethod
    def getSingleton(cls):
        if cls.Singleton is None:
            cls.Singleton = cls()
        return cls.Singleton

class ASGNodeAttributeDescriptor:
    def __init__(self) -> None:
        super().__init__()
        self.name: str = None

    def setName(self, name: str):
        self.name = name
        self.storageName = '_' + name

    def loadValueFrom(self, instance):
        return getattr(instance, self.storageName)
    
    def hasDefaultValueIn(self, instance) -> bool:
        return False
    
    def storeValueIn(self, value, instance):
        setattr(instance, self.storageName, value)

    def initializeWithConstructorValueOn(self, constructorValue, instance):
        raise Exception("Cannot initialize attribute %s during construction." % str(self.name))
    
    def initializeWithDefaultConstructorValueOn(self, instance):
        raise Exception("Cannot initialize attribute %s with default value during construction." % str(self.name))

    def isConstructionAttribute(self) -> bool:
        return False

    def isSpecialAttribute(self) -> bool:
        return False
    
    def isSequencingPredecessorAttribute(self) -> bool:
        return False

    def isSyntacticPredecessorAttribute(self) -> bool:
        return False
    
    def isSourceDerivationAttribute(self) -> bool:
        return False
    
    def isDataAttribute(self) -> bool:
        return False

    def isDataInputPort(self) -> bool:
        return False
    
    def isTypeInputPort(self) -> bool:
        return False
    
    def isSequencingDestinationPort(self) -> bool:
        return False
    
    def getNodeInputsOf(self, instance):
        return ()
    
    def __get__(self, instance, owner):
        return self.loadValueFrom(instance)
    
    def __set__(self, instance, value):
        raise Exception('Not supported')

class ASGNodeConstructionAttribute(ASGNodeAttributeDescriptor):
    def isConstructionAttribute(self) -> bool:
        return True

    def isNumberedConstructionAttribute(self) -> bool:
        return True
    
    def isComparedForUnification(self) -> bool:
        return True
    
    def hashFrom(self, instance) -> int:
        return hash(self.loadValueFrom(instance))
    
    def equalsFromAndFrom(self, first, second) -> bool:
        return self.loadValueFrom(first) == self.loadValueFrom(second)

    def initializeWithConstructorValueOn(self, constructorValue, instance):
        self.storeValueIn(constructorValue, instance)

class ASGNodeConstructionAttributeWithSourceDerivation(ASGNodeConstructionAttribute):
    def __init__(self) -> None:
        super().__init__()
        self.sourceDerivationStorageName = None

    def setName(self, name: str):
        super().setName(name)
        self.sourceDerivationStorageName = '_' + name + '_sourceDerivation'

    def loadSourceDerivationFrom(self, instance):
        return getattr(instance, self.sourceDerivationStorageName)

    def storeSourceDerivationIn(self, sourceDerivation, instance):
        return setattr(instance, self.sourceDerivationStorageName, sourceDerivation)

    def initializeWithConstructorValueOn(self, constructorValue, instance):
        self.storeValueIn(constructorValue.asASGNode(), instance)
        self.storeSourceDerivationIn(constructorValue.asASGNodeDerivation(), instance)

class ASGNodeDataAttribute(ASGNodeConstructionAttribute):
    def __init__(self, type, **kwArguments) -> None:
        super().__init__()
        self.type = type
        self.hasDefaultValue = False
        self.defaultValue = None
        self.isCompared = 'notCompared' not in kwArguments
        if 'default' in kwArguments:
            self.hasDefaultValue = True
            self.defaultValue = kwArguments['default']

    def isComparedForUnification(self) -> bool:
        return self.isCompared
    
    def hasDefaultValueIn(self, instance) -> bool:
        return self.hasDefaultValue and self.loadValueFrom(instance) == self.defaultValue

    def initializeWithDefaultConstructorValueOn(self, instance):
        if self.hasDefaultValue:
            self.storeValueIn(self.defaultValue, instance)
        else:
            super().initializeWithDefaultConstructorValueOn(self, instance)

    def isDataAttribute(self) -> bool:
        return True

class ASGNodeSourceDerivationAttribute(ASGNodeConstructionAttribute):
    def isConstructionAttribute(self) -> bool:
        return True

    def isSpecialAttribute(self) -> bool:
        return True

    def isSourceDerivationAttribute(self) -> bool:
        return True

    def isComparedForUnification(self) -> bool:
        return False

class ASGPredecessorAttribute(ASGNodeConstructionAttributeWithSourceDerivation):
    def isNumberedConstructionAttribute(self) -> bool:
        return False

    def initializeWithDefaultConstructorValueOn(self, instance):
        self.storeValueIn(None, instance)
        self.storeSourceDerivationIn(None, instance)

    def getNodeInputsOf(self, instance):
        value = self.loadValueFrom(instance)
        if value is None:
            return ()
        return (value,)
    
    def hashFrom(self, instance) -> int:
        return self.loadValueFrom(instance).unificationHash()
    
    def equalsFromAndFrom(self, first, second) -> bool:
        return self.loadValueFrom(first).unificationEquals(self.loadValueFrom(second))
    
class ASGSyntacticPredecessorAttribute(ASGPredecessorAttribute):
    def isSyntacticPredecessorAttribute(self) -> bool:
        return True

    def initializeWithConstructorValueOn(self, constructorValue, instance):
        if constructorValue is None:
            self.storeValueIn(None, instance)
            self.storeSourceDerivationIn(None, instance)
        else:
            super().initializeWithConstructorValueOn(constructorValue, instance)

class ASGSequencingPredecessorAttribute(ASGPredecessorAttribute):
    def isSequencingPredecessorAttribute(self) -> bool:
        return True

    def initializeWithConstructorValueOn(self, constructorValue, instance):
        if constructorValue is None:
            self.storeValueIn(None, instance)
            self.storeSourceDerivationIn(None, instance)
        else:
            self.storeValueIn(constructorValue.asASGSequencingNode(), instance)
            self.storeSourceDerivationIn(constructorValue.asASGSequencingNodeDerivation(), instance)
    
class ASGSequencingDestinationPort(ASGNodeConstructionAttributeWithSourceDerivation):
    def isSequencingDestinationPort(self) -> bool:
        return True

    def initializeWithConstructorValueOn(self, constructorValue, instance):
        self.storeValueIn(constructorValue.asASGSequencingNode(), instance)
        self.storeSourceDerivationIn(constructorValue.asASGSequencingNodeDerivation(), instance)

    def getNodeInputsOf(self, instance):
        return [self.loadValueFrom(instance)]
    
    def hashFrom(self, instance) -> int:
        return self.loadValueFrom(instance).unificationHash()
    
    def equalsFromAndFrom(self, first, second) -> bool:
        return self.loadValueFrom(first).unificationEquals(self.loadValueFrom(second))
    
class ASGNodeDataInputPort(ASGNodeConstructionAttributeWithSourceDerivation):
    def initializeWithConstructorValueOn(self, constructorValue, instance):
        self.storeValueIn(constructorValue.asASGDataNode(), instance)
        self.storeSourceDerivationIn(constructorValue.asASGDataNodeDerivation(), instance)

    def isDataInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        return [self.loadValueFrom(instance)]

    def hashFrom(self, instance) -> int:
        return self.loadValueFrom(instance).unificationHash()
    
    def equalsFromAndFrom(self, first, second) -> bool:
        return self.loadValueFrom(first).unificationEquals(self.loadValueFrom(second))
    
class ASGNodeOptionalDataInputPort(ASGNodeConstructionAttributeWithSourceDerivation):
    def initializeWithConstructorValueOn(self, constructorValue, instance):
        if constructorValue is None:
            self.storeValueIn(None, instance)
            self.storeSourceDerivationIn(None, instance)
        else:
            self.storeValueIn(constructorValue.asASGDataNode(), instance)
            self.storeSourceDerivationIn(constructorValue.asASGDataNodeDerivation(), instance)

    def isDataInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        value =  self.loadValueFrom(instance)
        if value is None:
            return ()
        return (value,)

    def hashFrom(self, instance) -> int:
        value = self.loadValueFrom(instance)
        if value is None:
            return hash(None)
        return value.unificationHash()
    
    def equalsFromAndFrom(self, first, second) -> bool:
        firstValue = self.loadValueFrom(first)
        secondValue = self.loadValueFrom(second)
        if firstValue is secondValue:
            return True
        if firstValue is None:
            return False
        return firstValue.unificationEquals(secondValue)

class ASGNodeDataInputPorts(ASGNodeConstructionAttributeWithSourceDerivation):
    def initializeWithConstructorValueOn(self, constructorValue, instance) -> bool:
        self.storeValueIn(tuple(map(lambda x: x.asASGDataNode(), constructorValue)), instance)
        self.storeSourceDerivationIn(tuple(map(lambda x: x.asASGDataNodeDerivation(), constructorValue)), instance)

    def isDataInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        return self.loadValueFrom(instance)

    def hashFrom(self, instance) -> int:
        result = hash(tuple)
        for value in self.loadValueFrom(instance):
            result ^= value.unificationHash()

        return value.unificationHash()
    
    def equalsFromAndFrom(self, first, second) -> bool:
        firstValue = self.loadValueFrom(first)
        secondValue = self.loadValueFrom(second)
        if len(firstValue) != len(secondValue):
            return False

        for i in range(len(firstValue)):
            if not firstValue[i].unificationEquals(secondValue[i]):
                return False

        return True

class ASGNodeDataAndSequencingInputPorts(ASGNodeConstructionAttributeWithSourceDerivation):
    def initializeWithConstructorValueOn(self, constructorValue, instance) -> bool:
        self.storeValueIn(tuple(map(lambda x: x.asASGNode(), constructorValue)), instance)
        self.storeSourceDerivationIn(tuple(map(lambda x: x.asASGNodeDerivation(), constructorValue)), instance)

    def isDataInputPort(self) -> bool:
        return True

    def isSequencingPredecessorAttribute(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        return self.loadValueFrom(instance)

    def hashFrom(self, instance) -> int:
        result = hash(tuple)
        for value in self.loadValueFrom(instance):
            result ^= value.unificationHash()

        return value.unificationHash()
    
    def equalsFromAndFrom(self, first, second) -> bool:
        firstValue = self.loadValueFrom(first)
        secondValue = self.loadValueFrom(second)
        if len(firstValue) != len(secondValue):
            return False

        for i in range(len(firstValue)):
            if not firstValue[i].unificationEquals(secondValue[i]):
                return False

        return True

class ASGNodeTypeInputNode(ASGNodeConstructionAttributeWithSourceDerivation):
    def initializeWithConstructorValueOn(self, constructorValue, instance) -> bool:
        self.storeValueIn(constructorValue.asASGTypeNode(), instance)
        self.storeSourceDerivationIn(constructorValue.asASGTypeNodeDerivation(), instance)

    def isTypeInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        return [self.loadValueFrom(instance)]
    
    def hashFrom(self, instance) -> int:
        return self.loadValueFrom(instance).unificationHash()
    
    def equalsFromAndFrom(self, first, second) -> bool:
        return self.loadValueFrom(first).unificationEquals(self.loadValueFrom(second))

class ASGNodeTypeInputNodes(ASGNodeConstructionAttributeWithSourceDerivation):
    def initializeWithConstructorValueOn(self, constructorValue, instance) -> bool:
        self.storeValueIn(tuple(map(lambda x: x.asASGTypeNode(), constructorValue)), instance)
        self.storeSourceDerivationIn(tuple(map(lambda x: x.asASGTypeNodeDerivation(), constructorValue)), instance)

    def isDataInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        return self.loadValueFrom(instance)

    def hashFrom(self, instance) -> int:
        result = hash(tuple)
        for value in self.loadValueFrom(instance):
            result ^= value.unificationHash()

        return value.unificationHash()
    
    def equalsFromAndFrom(self, first, second) -> bool:
        firstValue = self.loadValueFrom(first)
        secondValue = self.loadValueFrom(second)
        if len(firstValue) != len(secondValue):
            return False

        for i in range(len(firstValue)):
            if not firstValue[i].unificationEquals(secondValue[i]):
                return False

        return True
    
class ASGNodeMetaclass(type):
    def __new__(cls, name, bases, attributes):
        descriptors = []
        for base in bases:
            baseDescriptors = getattr(base, '__asgAttributeDescriptors__', None)
            if baseDescriptors is not None:
                descriptors += baseDescriptors

        for attributeName, attributeDescriptor in attributes.items():
            if not isinstance(attributeDescriptor, ASGNodeAttributeDescriptor):
                continue

            attributeDescriptor.setName(attributeName)
            descriptors.append(attributeDescriptor)

        specialAttributes: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isSpecialAttribute(), descriptors))
        syntacticPredecessors: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isSyntacticPredecessorAttribute(), descriptors))
        sequencingPredecessors: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isSequencingPredecessorAttribute(), descriptors))
        dataAttributes: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isDataAttribute(), descriptors))
        dataInputPorts: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isDataInputPort(), descriptors))
        typeInputPorts: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isTypeInputPort(), descriptors))
        destinationPorts: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isSequencingDestinationPort(), descriptors))

        numberedConstructionAttributes: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isConstructionAttribute() and desc.isNumberedConstructionAttribute(), descriptors))
        unnumberedConstructionAttributes: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isConstructionAttribute() and not desc.isNumberedConstructionAttribute(), descriptors))
        constructionAttributes = numberedConstructionAttributes + unnumberedConstructionAttributes

        constructionAttributeDictionary = {}
        for attr in constructionAttributes:
            constructionAttributeDictionary[attr.name] = attr
            
        nodeClass = super().__new__(cls, name, bases, attributes)
        nodeClass.__asgKindName__ = name.removeprefix('ASG').removesuffix('Node')
        nodeClass.__asgAttributeDescriptors__ = descriptors
        nodeClass.__asgSpecialAttributes__ = specialAttributes
        nodeClass.__asgSyntacticPredecessors__ = syntacticPredecessors
        nodeClass.__asgSequencingPredecessors__ = sequencingPredecessors
        nodeClass.__asgConstructionAttributes__ = constructionAttributes
        nodeClass.__asgConstructionAttributeDictionary__ = constructionAttributeDictionary
        nodeClass.__asgDataAttributes__ = dataAttributes
        nodeClass.__asgDataInputPorts__ = dataInputPorts
        nodeClass.__asgTypeInputPorts__ = typeInputPorts
        nodeClass.__asgDestinationPorts__ = destinationPorts
        return nodeClass

class ASGNode(metaclass = ASGNodeMetaclass):
    def __init__(self, *positionalArguments, **kwArguments) -> None:
        super().__init__()

        self.__hashValueCache__ = None
        self.__betaReplaceableDependencies__ = None

        constructionAttributes = self.__class__.__asgConstructionAttributes__
        constructionAttributeDictionary = self.__class__.__asgConstructionAttributeDictionary__
        if len(positionalArguments) > len(constructionAttributes):
            raise Exception('Excess number of construction arguments.')
        
        for i in range(len(positionalArguments)):
            constructionAttributes[i].initializeWithConstructorValueOn(positionalArguments[i], self)
        for i in range(len(positionalArguments), len(constructionAttributes)):
            constructionAttributes[i].initializeWithDefaultConstructorValueOn(self)

        for key, value in kwArguments.items():
            if key not in constructionAttributeDictionary:
                raise Exception('Failed to find attribute %s in %s' % (str(key), repr(self.__class__)))
            constructionAttributeDictionary[key].initializeWithConstructorValueOn(value, self)

    def unificationHash(self) -> int:
        if self.__hashValueCache__ is not None:
            return self.__hashValueCache__

        self.__hashValueCache__ = hash(self.__class__)
        constructionAttributes = self.__class__.__asgConstructionAttributes__
        for attribute in constructionAttributes:
            if attribute.isComparedForUnification():
                self.__hashValueCache__ ^= attribute.hashFrom(self)
        return self.__hashValueCache__
    
    def unificationEquals(self, other) -> bool:
        if self is other: return True
        if self.__class__ != other.__class__:
            return False

        constructionAttributes = self.__class__.__asgConstructionAttributes__
        for attribute in constructionAttributes:
            if attribute.isComparedForUnification():
                if not attribute.equalsFromAndFrom(self, other):
                    return False

        return True

    def asASGNode(self):
        return self

    def asASGNodeDerivation(self):
        return ASGNodeNoDerivation.getSingleton()

    def asASGDataNode(self):
        return self.asASGNode()

    def asASGDataNodeDerivation(self):
        return self.asASGNodeDerivation()

    def asASGTypeNode(self):
        return self.asASGNode()

    def asASGTypeNodeDerivation(self):
        return self.asASGNodeDerivation()
    
    def isBetaReplaceableNode(self) -> bool:
        return False

    def isTypeNode(self) -> bool:
        return False

    def isTypeUniverseNode(self) -> bool:
        return False

    def isPureDataNode(self) -> bool:
        raise Exception("Subclass responsibility isPureDataNode")
    
    def isSequencingNode(self) -> bool:
        return False

    def isTypedLiteralNode(self) -> bool:
        return False
    
    def asASGSequencingNode(self):
        if self.isPureDataNode():
            return None

        return self.asASGNode()

    def asASGSequencingNodeDerivation(self):
        if self.isPureDataNode():
            return None

        return self.asASGNodeDerivation()

    def explicitDestinations(self):
        for port in self.__class__.__asgDestinationPorts__:
            for predecessor in port.getNodeInputsOf(self):
                yield predecessor

    def sequencingDependencies(self):
        for port in self.__class__.__asgSequencingPredecessors__:
            for predecessor in port.getNodeInputsOf(self):
                yield predecessor

    def syntacticDependencies(self):
        for port in self.__class__.__asgSyntacticPredecessors__:
            for predecessor in port.getNodeInputsOf(self):
                yield predecessor

    def effectDependencies(self):
        return []

    def dataDependencies(self):
        for port in self.__class__.__asgDataInputPorts__:
            for dataInput in port.getNodeInputsOf(self):
                yield dataInput

    def typeDependencies(self):
        for port in self.__class__.__asgTypeInputPorts__:
            for typeInput in port.getNodeInputsOf(self):
                yield typeInput

    def allDependencies(self):
        for dependency in self.sequencingDependencies():
            yield dependency
        for dependency in self.syntacticDependencies():
            yield dependency
        for dependency in self.effectDependencies():
            yield dependency
        for dependency in self.dataDependencies():
            yield dependency
        for dependency in self.typeDependencies():
            yield dependency
    
    def printNameWithDataAttributes(self) -> str:
        result = self.__class__.__asgKindName__
        attributes: list[ASGNodeAttributeDescriptor] = self.__class__.__asgDataAttributes__
        destIndex = 0;
        for attribute in attributes:
            if attribute.hasDefaultValueIn(self):
                continue

            if destIndex == 0:
                result += '('
            else:
                result += ', '

            result += attribute.name
            result += ' = '
            result += repr(attribute.loadValueFrom(self))
            destIndex += 1

        if destIndex != 0:
            result += ')'
                
        return result

    def printNameWithComparedAttributes(self) -> str:
        result = self.__class__.__asgKindName__
        attributes: list[ASGNodeAttributeDescriptor] = self.__class__.__asgConstructionAttributes__
        destIndex = 0;
        for attribute in attributes:
            if not attribute.isComparedForUnification():
                continue

            if attribute.hasDefaultValueIn(self):
                continue

            if destIndex == 0:
                result += '('
            else:
                result += ', '

            result += attribute.name
            result += ' = '
            attributeValue = attribute.loadValueFrom(self)
            if isinstance(attributeValue, tuple):
                result += '('
                for i in range(len(attributeValue)):
                    if i > 0:
                        result += ', '
                    result += str(attributeValue[i])
                result += ')'
            else:
                result += str(attributeValue)
            result += ('@%x' % attribute.hashFrom(self))
            destIndex += 1

        if destIndex != 0:
            result += ')'
                
        return result

    def prettyPrintNameWithDataAttributes(self) -> str:
        return self.printNameWithDataAttributes()
    
    def hasSequencingPredecessorOf(self, predecessor) -> bool:
        return False
    
    def isSequencingNodeForExpression(self, expression) -> bool:
        return False
    
    def __str__(self) -> str:
        return self.printNameWithDataAttributes()
    
    def isKindOf(self, kind):
        return isinstance(self, kind)

    def expandPatternWithValueAt(self, expander, value, location):
        return ASGSyntaxErrorNode(ASGNodeExpansionDerivation(expander, location), 'Not a valid pattern for expanding.', [self, location])

    def expandSyntaxApplicationNode(self, expander, applicationNode):
        # Expand the arguments for making the error messages.
        for argument in applicationNode.arguments:
            expander(argument)
        
        return expander.makeErrorAtNode('Cannot apply non-functional value of type %s.' % str(self), applicationNode)

    def betaReplaceableDependencies(self):
        if self.__betaReplaceableDependencies__ is not None:
            return self.__betaReplaceableDependencies__
        
        self.__betaReplaceableDependencies__ = set()
        for dependency in self.allDependencies():
            self.__betaReplaceableDependencies__ += dependency.betaReplaceableDependencies()
        return self.__betaReplaceableDependencies__

class ASGUnificationComparisonNode:
    def __init__(self, node) -> None:
        self.node = node

    def __eq__(self, other: object) -> bool:
        return self.node.unificationEquals(other.node)
    
    def __hash__(self) -> int:
        return self.node.unificationHash()

class ASGSyntaxNode(ASGNode):
    sourceDerivation = ASGNodeSourceDerivationAttribute()
    syntacticPredecessor = ASGSyntacticPredecessorAttribute()

    def isPureDataNode(self) -> bool:
        return True

    def asASGNodeDerivation(self):
        return self.sourceDerivation

class ASGSyntaxErrorNode(ASGSyntaxNode):
    message = ASGNodeDataAttribute(int)
    innerNodes = ASGNodeDataInputPorts()

class ASGSyntaxLiteralNode(ASGSyntaxNode):
    pass

class ASGSyntaxLiteralCharacterNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGSyntaxLiteralIntegerNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGSyntaxLiteralFloatNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(float)

class ASGSyntaxLiteralStringNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(str)

class ASGSyntaxLiteralSymbolNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(str)

class ASGSyntaxApplicationNode(ASGSyntaxNode):
    functional = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()
    kind = ASGNodeDataAttribute(int, default = 0)

class ASGSyntaxAssignmentNode(ASGSyntaxNode):
    store = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()

class ASGSyntaxBindableNameNode(ASGSyntaxNode):
    typeExpression = ASGNodeOptionalDataInputPort()
    nameExpression = ASGNodeOptionalDataInputPort()
    isImplicit = ASGNodeDataAttribute(bool, default = False)
    isExistential = ASGNodeDataAttribute(bool, default = False)
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    isMutable = ASGNodeDataAttribute(bool, default = False)
    hasPostTypeExpression = ASGNodeDataAttribute(bool, default = False)

    def expandPatternWithValueAt(self, expander, value, location):
        return ASGSyntaxBindingDefinitionNode(ASGNodeExpansionDerivation(expander, location),
                self.typeExpression, self.nameExpression, value,
                self.isMutable)

    def parseAndUnpackArgumentsPattern(self):
        return [self], self.isExistential, self.isVariadic
    
class ASGSyntaxBindPatternNode(ASGSyntaxNode):
    pattern = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()
    allowsRebind = ASGNodeDataAttribute(bool, default = False)

class ASGSyntaxBinaryExpressionSequenceNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntaxBindingDefinitionNode(ASGSyntaxNode):
    typeExpression = ASGNodeOptionalDataInputPort()
    nameExpression = ASGNodeOptionalDataInputPort()
    valueExpression = ASGNodeDataInputPort()
    isMutable = ASGNodeDataAttribute(bool, default = False)
    allowsRebind = ASGNodeDataAttribute(bool, default = False)

class ASGSyntaxBlockNode(ASGSyntaxNode):
    functionType = ASGNodeDataInputPort()
    body = ASGNodeDataInputPorts()

class ASGSyntaxIdentifierReferenceNode(ASGSyntaxNode):
    value = ASGNodeDataAttribute(str)

class ASGSyntaxLexicalBlockNode(ASGSyntaxNode):
    body = ASGNodeDataInputPort()

class ASGSyntaxMessageSendNode(ASGSyntaxNode):
    receiver = ASGNodeOptionalDataInputPort()
    selector = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()

class ASGSyntaxDictionaryNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntaxFunctionalDependentTypeNode(ASGSyntaxNode):
    argumentPattern = ASGNodeOptionalDataInputPort()
    resultType = ASGNodeOptionalDataInputPort()
    callingConvention = ASGNodeDataAttribute(str, default = None)

    def constructLambdaWithBody(self, derivation, nameExpression, body, isFixpoint):
        bodyOrInnerLambda = body
        if self.resultType is not None and self.resultType.__class__ == ASGSyntaxFunctionalDependentTypeNode:
            bodyOrInnerLambda = self.resultType.constructLambdaWithBody(derivation, None, body, False)

        argumentNodes = []
        isExistential = False
        isVariadic = False
        if self.argumentPattern is not None:
            argumentNodes, isExistential, isVariadic = self.argumentPattern.parseAndUnpackArgumentsPattern()

        return ASGSyntaxLambdaNode(derivation, nameExpression, argumentNodes, self.resultType, bodyOrInnerLambda, isVariadic = isVariadic, isFixpoint = isFixpoint, callingConvention = self.callingConvention)

class ASGSyntaxFunctionNode(ASGSyntaxNode):
    nameExpression = ASGNodeOptionalDataInputPort()
    functionalType = ASGNodeDataInputPort()
    body = ASGNodeDataInputPort()
    isFixpoint = ASGNodeDataAttribute(bool, default = False)

class ASGSyntaxLambdaNode(ASGSyntaxNode):
    nameExpression = ASGNodeOptionalDataInputPort()
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeOptionalDataInputPort()
    body = ASGNodeDataInputPort()
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    isFixpoint = ASGNodeDataAttribute(bool, default = False)
    callingConvention = ASGNodeDataAttribute(str, default = None)

class ASGSyntaxPiNode(ASGSyntaxNode):
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeOptionalDataInputPort()
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    callingConvention = ASGNodeDataAttribute(str, default = None)

class ASGSyntaxSigmaNode(ASGSyntaxNode):
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeOptionalDataInputPort()
    isVariadic = ASGNodeDataAttribute(bool, default = False)

class ASGSyntaxSequenceNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntaxTupleNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

    def parseAndUnpackArgumentsPattern(self):
        isExistential = False
        isVariadic = False
        if len(self.elements) == 1 and self.elements[0].isKindOf(ASGSyntaxBindableNameNode):
            isExistential = self.elements[0].isExistential
        if len(self.elements) > 0 and self.elements[-1].isKindOf(ASGSyntaxBindableNameNode):
            isVariadic = self.elements[-1].isVariadic
        return self.elements, isExistential, isVariadic

class ASGParseTreeFrontEnd(ParseTreeVisitor):
    def __init__(self):
        self.lastVisitedNode = None

    def visitNode(self, node: ParseTreeNode):
        self.lastVisitedNode = super().visitNode(node)
        return self.lastVisitedNode

    def visitNodeWithoutSequencing(self, node: ParseTreeNode):
        lastVisitedNode = None
        result = self.visitNode(node)
        self.lastVisitedNode = lastVisitedNode
        return result

    def transformNodesWithoutSequencing(self, nodes: list[ParseTreeNode]):
        lastVisitedNode = None
        result = self.transformNodes(nodes)
        self.lastVisitedNode = lastVisitedNode
        return result

    def visitOptionalNodeWithoutSequencing(self, node: ParseTreeNode):
        if node is None:
            return None
        return self.visitNodeWithoutSequencing(node)

    def visitErrorNode(self, node: ParseTreeErrorNode):
        return ASGSyntaxErrorNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.message, self.transformNodes(node.innerNodes), syntacticPredecessor = self.lastVisitedNode)

    def visitApplicationNode(self, node: ParseTreeApplicationNode):
        return ASGSyntaxApplicationNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functional), self.transformNodesWithoutSequencing(node.arguments), node.kind, syntacticPredecessor = self.lastVisitedNode)

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        return ASGSyntaxAssignmentNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNodeWithoutSequencing(node.store), self.visitNodeWithoutSequencing(node.value), syntacticPredecessor = self.lastVisitedNode)

    def visitBindPatternNode(self, node: ParseTreeBindPatternNode):
        return ASGSyntaxBindPatternNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNodeWithoutSequencing(node.pattern), self.visitNode(node.value), syntacticPredecessor = self.lastVisitedNode, allowsRebind = True)

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        return ASGSyntaxBinaryExpressionSequenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitBindableNameNode(self, node: ParseTreeBindableNameNode):
        return ASGSyntaxBindableNameNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.typeExpression), self.visitOptionalNode(node.nameExpression), node.isImplicit, node.isExistential, node.isVariadic, node.isMutable, node.hasPostTypeExpression, syntacticPredecessor = self.lastVisitedNode)

    def visitBlockNode(self, node: ParseTreeBlockNode):
        return ASGSyntaxBlockNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functionType), self.visitNode(node.body), syntacticPredecessor = self.lastVisitedNode)

    def visitDictionaryNode(self, node: ParseTreeDictionaryNode):
        return ASGSyntaxDictionaryNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitFunctionalDependentTypeNode(self, node: ParseTreeFunctionalDependentTypeNode):
        return ASGSyntaxFunctionalDependentTypeNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNodeWithoutSequencing(node.argumentPattern), self.visitOptionalNodeWithoutSequencing(node.resultType), syntacticPredecessor = self.lastVisitedNode)

    def visitIdentifierReferenceNode(self, node: ParseTreeIdentifierReferenceNode):
        return ASGSyntaxIdentifierReferenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLexicalBlockNode(self, node: ParseTreeLexicalBlockNode):
        return ASGSyntaxLexicalBlockNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.body), syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralCharacterNode(self, node: ParseTreeLiteralCharacterNode):
        return ASGSyntaxLiteralCharacterNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralFloatNode(self, node: ParseTreeLiteralFloatNode):
        return ASGSyntaxLiteralFloatNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralIntegerNode(self, node: ParseTreeLiteralIntegerNode):
        return ASGSyntaxLiteralIntegerNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralSymbolNode(self, node: ParseTreeLiteralSymbolNode):
        return ASGSyntaxLiteralSymbolNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralStringNode(self, node: ParseTreeLiteralStringNode):
        return ASGSyntaxLiteralStringNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitMessageSendNode(self, node: ParseTreeMessageSendNode):
        return ASGSyntaxMessageSendNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.receiver), self.visitNode(node.selector), self.transformNodesWithoutSequencing(node.arguments), syntacticPredecessor = self.lastVisitedNode)

    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        return ASGSyntaxSequenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitTupleNode(self, node: ParseTreeTupleNode):
        return ASGSyntaxTupleNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

class ASGTypecheckedNode(ASGNode):
    sourceDerivation = ASGNodeSourceDerivationAttribute()

    def asASGNodeDerivation(self):
        return self.sourceDerivation

class ASGSequencingNode(ASGTypecheckedNode):
    def isPureDataNode(self) -> bool:
        return False

    def isSequencingNode(self) -> bool:
        return True

class ASGEntryPointNode(ASGSequencingNode):
    def isEntryPointNode(self) -> bool:
        return True

class ASGExitPointNode(ASGSequencingNode):
    predecessor = ASGSequencingPredecessorAttribute()
    expression = ASGNodeDataInputPort()

    def isExitPointNode(self) -> bool:
        return True

    def hasSequencingPredecessorOf(self, predecessor) -> bool:
        return self is predecessor or self.predecessor is predecessor
    
    def isSequencingNodeForExpression(self, expression) -> bool:
        return self.expression is expression
    
class ASGSequenceExpressionNode(ASGSequencingNode):
    predecessor = ASGSequencingPredecessorAttribute()
    expression = ASGNodeDataInputPort()

    def getTypeInEnvironment(self, environment) -> ASGTypecheckedNode:
        return self.expression.getTypeInEnvironment(environment)
    
    def asASGDataNode(self):
        return self.expression.asASGDataNode()
    
    def asASGDataNodeDerivation(self):
        return self.expression.asASGDataNodeDerivation()
    
    def asASGTypeNode(self):
        return self.expression.asASGTypeNode()
    
    def asASGTypeNodeDerivation(self):
        return self.expression.asASGTypeNodeDerivation()
    
    def hasSequencingPredecessorOf(self, predecessor) -> bool:
        return self is predecessor or self.predecessor is predecessor
    
    def isSequencingNodeForExpression(self, expression) -> bool:
        return self.expression is expression

class ASGTypedExpressionNode(ASGTypecheckedNode):
    type = ASGNodeTypeInputNode()

    def isTypeNode(self) -> bool:
        return self.type.isTypeUniverseNode()

    def getTypeInEnvironment(self, environment) -> ASGTypecheckedNode:
        return self.type

class ASGTypedDataExpressionNode(ASGTypedExpressionNode):
    def isPureDataNode(self) -> bool:
        return True

class ASGErrorNode(ASGTypedDataExpressionNode):
    message = ASGNodeDataAttribute(str)

class ASGLiteralNode(ASGTypedDataExpressionNode):
    def isTypedLiteralNode(self) -> bool:
        return True
    
class ASGLiteralCharacterNode(ASGLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGLiteralIntegerNode(ASGLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGLiteralFloatNode(ASGLiteralNode):
    value = ASGNodeDataAttribute(float)

class ASGLiteralSymbolNode(ASGLiteralNode):
    value = ASGNodeDataAttribute(str)

class ASGLiteralUnitNode(ASGLiteralNode):
    pass

class ASGTypeNode(ASGTypecheckedNode):
    def isTypeNode(self) -> bool:
        return True

    def isPureDataNode(self) -> bool:
        return True

    def getTypeUniverseIndex(self) -> int:
        return 0

    def getTypeInEnvironment(self, environment) -> ASGTypecheckedNode:
        return environment.getTopLevelTargetEnvironment().getTypeUniverseWithIndex(self.getTypeUniverseIndex())

class ASGBetaReplaceableNode(ASGTypedDataExpressionNode):
    def isBetaReplaceableNode(self) -> bool:
        return True
    
    def betaReplaceableDependencies(self):
        return ()

class ASGArgumentNode(ASGBetaReplaceableNode):
    index = ASGNodeDataAttribute(int, default = 0)
    name = ASGNodeDataAttribute(str, default = None, notCompared = True)
    isImplicit = ASGNodeDataAttribute(bool, default = False)

class ASGCapturedValueNode(ASGBetaReplaceableNode):
    pass

class ASGBaseTypeNode(ASGTypeNode):
    name = ASGNodeDataAttribute(str)

    def prettyPrintNameWithDataAttributes(self):
        if self.name is not None:
            return self.name
        else:
            return super().prettyPrintNameWithDataAttributes()

class ASGUnitTypeNode(ASGBaseTypeNode):
    pass

class ASGBottomTypeNode(ASGBaseTypeNode):
    pass

class ASGPrimitiveType(ASGBaseTypeNode):
    size = ASGNodeDataAttribute(int)
    alignment = ASGNodeDataAttribute(int)

class ASGPrimitiveCharacterType(ASGPrimitiveType):
    pass

class ASGPrimitiveIntegerType(ASGPrimitiveType):
    isSigned = ASGNodeDataAttribute(int)
    pass

class ASGPrimitiveFloatType(ASGPrimitiveType):
    pass

class ASGAnyTypeUniverseNode(ASGBaseTypeNode):
    def isTypeUniverseNode(self) -> bool:
        return True
    
class ASGTypeUniverseNode(ASGTypeNode):
    index = ASGNodeDataAttribute(int)

    def isTypeUniverseNode(self) -> bool:
        return True

    def getTypeInEnvironment(self, environment) -> ASGTypecheckedNode:
        return environment.getTopLevelTargetEnvironment().getTypeUniverseWithIndex(self.index + 1)

class ASGProductTypeNode(ASGTypeNode):
    elements = ASGNodeTypeInputNodes()

class ASGTupleNode(ASGTypedDataExpressionNode):
    elements = ASGNodeDataInputPorts()

class ASGLambdaNode(ASGTypedDataExpressionNode):
    arguments = ASGNodeDataInputPorts()
    entryPoint = ASGSequencingDestinationPort()
    exitPoints = ASGNodeDataAndSequencingInputPorts()
    callingConvention = ASGNodeDataAttribute(str, default = None)

class ASGApplicationNode(ASGTypedDataExpressionNode):
    functional = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()

class ASGTopLevelScriptNode(ASGTypedDataExpressionNode):
    entryPoint = ASGSequencingDestinationPort()
    exitPoints = ASGNodeDataAndSequencingInputPorts()

class ASGSumTypeNode(ASGTypeNode):
    elements = ASGNodeTypeInputNodes()

class ASGSigmaNode(ASGTypeNode):
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeDataInputPort()

class ASGPiNode(ASGTypeNode):
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeDataInputPort()
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    callingConvention = ASGNodeDataAttribute(str, default = None)

    def expandSyntaxApplicationNode(self, expander, applicationNode):
        return expander.expandDependentApplicationWithType(applicationNode, self)
    
def asgTopoSortTraversal(aBlock, node: ASGNode):
    visited = set()
    def visitNode(node):
        if node in visited:
            return
        
        visited.add(node)
        for dependency in node.allDependencies():
            visitNode(dependency)
        aBlock(node)

    visitNode(node)

def asgTopoSort(node: ASGNode):
    sorted = []
    if node is not None:
        asgTopoSortTraversal(sorted.append, node)
    return sorted

def asgToDot(node: ASGNode):
    sortedNodes = asgTopoSort(node)
    nodeToNameDictionary = {}
    nodeCount = 0
    result = 'digraph {\n'
    for node in sortedNodes:
        nodeName = 'N%d' % nodeCount
        nodeToNameDictionary[node] = nodeName
        result += '  N%d [label="%s"]\n' % (nodeCount, node.prettyPrintNameWithDataAttributes().replace('\\', '\\\\').replace('"', '\\"'))
        nodeCount += 1

    for node in sortedNodes:
        nodeName = nodeToNameDictionary[node]
        for dependency in node.sequencingDependencies():
            dependencyName = nodeToNameDictionary[dependency]
            result += '  %s -> %s [color = blue]\n' % (nodeName, dependencyName)
        for dependency in node.syntacticDependencies():
            dependencyName = nodeToNameDictionary[dependency]
            result += '  %s -> %s [color = blue]\n' % (nodeName, dependencyName)
        for dependency in node.effectDependencies():
            dependencyName = nodeToNameDictionary[dependency]
            result += '  %s -> %s [color = red]\n' % (nodeName, dependencyName)
        for dependency in node.dataDependencies():
            dependencyName = nodeToNameDictionary[dependency]
            result += '  %s -> %s [color = green]\n' % (nodeName, dependencyName)
        for dependency in node.typeDependencies():
            dependencyName = nodeToNameDictionary[dependency]
            result += '  %s -> %s [color = yellow]\n' % (nodeName, dependencyName)

        for destination in node.explicitDestinations():
            destinationName = nodeToNameDictionary[destination]
            result += '  %s -> %s [color = cyan]\n' % (nodeName, destinationName)

    result += '}\n'
    return result

def asgToDotFileNamed(node: ASGNode, filename: str):
    dotData = asgToDot(node)
    with open(filename, "w") as f:
        f.write(dotData)

class ASGPatternMatchingPattern(ABC):
    @abstractmethod
    def matchesNode(self, node: ASGNode):
        pass

    @abstractmethod
    def getExpectedKind(self) -> type:
        pass

    @abstractmethod
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        pass

class ASGPatternMatchingNodeKindPattern(ASGPatternMatchingPattern):
    def __init__(self, kind: type, function) -> None:
        super().__init__()
        self.kind = kind
        self.function = function

    def getExpectedKind(self) -> type:
        return self.kind

    def matchesNode(self, node):
        return True

    def __call__(self, algorithm, expansionResult, *args: Any, **kwArguments) -> Any:
        return self.function(algorithm, *args, **kwArguments)

class ASGPatternMatchingNodeKindPatternWithPredicate(ASGPatternMatchingNodeKindPattern):
    def __init__(self, kind: type, predicate, function) -> None:
        super().__init__(kind, function)
        self.predicate = predicate

    def matchesNode(self, node):
        return self.predicate(node)

def asgPatternMatchingOnNodeKind(kind: type, when = None):
    def makePattern(function):
        if when is not None:
            return ASGPatternMatchingNodeKindPatternWithPredicate(kind, when, function)
        else:
            return ASGPatternMatchingNodeKindPattern(kind, function)
    return makePattern

class ASGUnifiedNodeValue:
    def __init__(self, node: ASGNode, derivation: ASGNodeDerivation) -> None:
        self.node = node
        self.derivation = derivation

    def asASGNode(self) -> ASGNode:
        return self.node
    
    def asASGNodeDerivation(self) -> ASGNodeDerivation:
        return self.derivation

    def asASGDataNode(self):
        return self.node.asASGDataNode()

    def asASGDataNodeDerivation(self):
        return self.node.asASGDataNodeDerivation()
    
    def asASGSequencingNode(self):
        return self.node.asASGSequencingNode()

    def asASGSequencingNodeDerivation(self):
        return self.node.asASGSequencingNodeDerivation()
    
    def asASGTypeNode(self):
        return self.node.asASGTypeNode()

    def asASGTypeNodeDerivation(self):
        return self.node.asASGTypeNodeDerivation()
    
    def isSequencingNode(self):
        return self.node.isSequencingNode()

    def hasSequencingPredecessorOf(self, predecessor):
        return self.node.hasSequencingPredecessorOf(predecessor)
    
class ASGDynamicProgrammingAlgorithmMetaclass(type):
    def __new__(cls, name, bases, attributes):
        patterns: list[ASGPatternMatchingNodeKindPattern] = []
        patternKindDictionary = {}
        for value in attributes.values():
            if isinstance(value, ASGPatternMatchingPattern):
                patterns.append(value)

        for pattern in patterns:
            patternKind = pattern.getExpectedKind()
            if patternKind not in patternKindDictionary:
                patternKindDictionary[patternKind] = []
            patternKindDictionary[patternKind].append(pattern)

        algorithm = super().__new__(cls, name, bases, attributes)
        algorithm.__asgDPAPatterns__ = patterns
        algorithm.__asgDPAPatternKindDictionary__ = patternKindDictionary
        return algorithm

class ASGDynamicProgrammingAlgorithmNodeExpansionResult:
    def __init__(self, incomingDelegatingExpansion, node: ASGNode) -> None:
        self.incomingDelegatingExpansion: ASGDynamicProgrammingAlgorithmNodeExpansionResult = incomingDelegatingExpansion
        self.node = node
        self.hasFinished = False
        self.result = None

    def finishWithValue(self, resultValue):
        if self.hasFinished:
            if resultValue != self.result:
                raise Exception("Expansion of %s has diverging result values." % (self.node))
            return self.result

        self.hasFinished = True
        self.result = resultValue
        if self.incomingDelegatingExpansion is not None:
            self.incomingDelegatingExpansion.finishWithValue(resultValue)
        return resultValue
    
class ASGDynamicProgrammingAlgorithm(metaclass = ASGDynamicProgrammingAlgorithmMetaclass):
    def __init__(self) -> None:
        self.processedNodes = {}

    def fromNodeContinueExpanding(self, incomingDelegatingNode: ASGNode, node: ASGNode):
        expansionResult = self.processedNodes.get(node, None)
        if expansionResult is not None:
            if not expansionResult.hasFinished:
                raise Exception('Circular dependency in expansion of node %s' % str(node))

            return expansionResult.result

        patternKindDictionary = self.__class__.__asgDPAPatternKindDictionary__
        currentClass = node.__class__
        while currentClass is not None:
            patterns: list[ASGPatternMatchingNodeKindPattern] | None = patternKindDictionary.get(currentClass, None)
            if patterns is not None:
                for pattern in patterns:
                    if pattern.matchesNode(node):
                        incomingExpansion = None
                        if incomingDelegatingNode is not None:
                            incomingExpansion = self.processedNodes[incomingDelegatingNode]

                        expansionResult = ASGDynamicProgrammingAlgorithmNodeExpansionResult(incomingExpansion, node)
                        self.processedNodes[node] = expansionResult
                        return expansionResult.finishWithValue(pattern(self, expansionResult, node))

            if len(currentClass.__bases__) != 0:
                currentClass = currentClass.__bases__[0]
            else:
                currentClass = None
        raise Exception("Failed to find matching pattern for %s in %s." % (str(node), str(self)))
    
    def __call__(self, node: ASGNode) -> Any:
        return self.fromNodeContinueExpanding(None, node)

class ASGEnvironment(ABC):
    @abstractmethod
    def getTopLevelTargetEnvironment(self):
        pass

    @abstractmethod
    def lookSymbolBindingListRecursively(self, symbol: str):
        pass

    def isLexicalEnvironment(self):
        return False

    def isScriptEnvironment(self):
        return False
    
    def childWithSymbolBinding(self, symbol: str, binding: ASGNode):
        return ASGChildEnvironmentWithBindings(self).childWithSymbolBinding(symbol, binding)

class ASGTopLevelTargetEnvironment(ASGEnvironment):
    def __init__(self, target: CompilationTarget) -> None:
        super().__init__()
        self.target = target
        self.symbolTable = {}
        topLevelDerivation = ASGNodeNoDerivation.getSingleton()
        self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'Integer'))
        self.addBaseType(ASGBottomTypeNode(topLevelDerivation, 'Abort'))
        self.addBaseType(ASGUnitTypeNode(topLevelDerivation, 'Void'))
        self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'Symbol'))
        self.addBaseType(ASGAnyTypeUniverseNode(topLevelDerivation, 'Type'))
        self.addBaseType(ASGPrimitiveCharacterType(topLevelDerivation, 'Char8',  1, 1))
        self.addBaseType(ASGPrimitiveCharacterType(topLevelDerivation, 'Char16',  2, 2))
        self.addBaseType(ASGPrimitiveCharacterType(topLevelDerivation, 'Char32',  4, 4))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Int8',  1, 1, True))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Int16', 2, 2, True))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Int32', 4, 4, True))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Int64', 8, 8, True))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'UInt8',  1, 1, False))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'UInt16', 2, 2, False))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'UInt32', 4, 4, False))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'UInt64', 8, 8, False))
        self.addBaseType(ASGPrimitiveIntegerType(topLevelDerivation, 'Size', target.pointerSize, target.pointerAlignment, False))
        self.addBaseType(ASGPrimitiveFloatType(topLevelDerivation, 'Float32', 4, 4))
        self.addBaseType(ASGPrimitiveFloatType(topLevelDerivation, 'Float64', 8, 8))

    def addBaseType(self, baseType: ASGBaseTypeNode):
        self.addSymbolValue(baseType.name, baseType)

    def addSymbolValue(self, name: str, value: ASGNode):
        if name is not None:
            self.symbolTable[name] = [value] + self.symbolTable.get(name, [])

    def lookLastBindingOf(self, name: str):
        if not name in self.symbolTable:
            return None
        return self.symbolTable[name][0]

    def getTopLevelTargetEnvironment(self):
        return self
    
    def getTypeUniverseWithIndex(self, index):
        if index in self.typeUniverseIndexCache:
            return self.typeUniverseIndexCache[index]
        
        universe = ASGTypeUniverseNode(index)
        self.typeUniverseIndexCache[universe]
        return universe

    def lookSymbolBindingListRecursively(self, symbol: str):
        return self.symbolTable.get(symbol, [])

    @classmethod
    def getForTarget(cls, target: CompilationTarget):
        if hasattr(target, 'asgTopLevelTargetEnvironment'):
            return target.asgTopLevelTargetEnvironment

        topLevelEnvironment = cls(target)
        target.asgTopLevelTargetEnvironment = topLevelEnvironment
        return topLevelEnvironment

class ASGChildEnvironment(ASGEnvironment):
    def __init__(self, parent: ASGEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__()
        self.parent = parent
        self.sourcePosition = sourcePosition
        self.topLevelTargetEnvironment = parent.getTopLevelTargetEnvironment()
    
    def getTopLevelTargetEnvironment(self):
        return self.topLevelTargetEnvironment

    def lookSymbolBindingListRecursively(self, symbol: str):
        return self.parent.lookSymbolBindingListRecursively(symbol)

class ASGChildEnvironmentWithBindings(ASGChildEnvironment):
    def __init__(self, parent: ASGEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent, sourcePosition)
        self.symbolTable = {}

    def postCopy(self):
        self.symbolTable = dict(self.symbolTable)

    def addSymbolBinding(self, symbol: str, binding: ASGNode):
        if symbol is not None:
            self.symbolTable[symbol] = [binding] + self.symbolTable.get(symbol, [])

    def childWithSymbolBinding(self, symbol: str, binding: ASGNode):
        child = copy.copy(self)
        child.postCopy()
        child.addSymbolBinding(symbol, binding)
        return child

    def lookSymbolBindingListRecursively(self, symbol: str):
        return self.symbolTable.get(symbol, []) + self.parent.lookSymbolBindingListRecursively(symbol)

class ASGLexicalEnvironment(ASGChildEnvironment):
    def isLexicalEnvironment(self):
        return True

class ASGFunctionalAnalysisEnvironment(ASGLexicalEnvironment):
    def __init__(self, parent: ASGEnvironment, sourcePosition: SourcePosition = None) -> None:
        super().__init__(parent, sourcePosition)
        self.arguments = []
        self.symbolTable = {}

    def addArgumentBinding(self, argument: ASGArgumentNode):
        self.arguments.append(argument)
        if argument.name is not None:
            self.symbolTable[argument.name] = [argument] + self.symbolTable.get(argument.name, [])

    def lookSymbolBindingListRecursively(self, symbol: str):
        return self.symbolTable.get(symbol, []) + self.parent.lookSymbolBindingListRecursively(symbol)

class ASGScriptEnvironment(ASGLexicalEnvironment):
    def __init__(self, parent: ASGEnvironment, sourcePosition: SourcePosition = None, scriptDirectory = '', scriptName = 'script') -> None:
        super().__init__(parent, sourcePosition)
        self.scriptDirectory = scriptDirectory
        self.scriptName = scriptName

    def isScriptEnvironment(self):
        return True

class ASGBuilderWithGVN:
    def __init__(self, parentBuilder, topLevelEnvironment: ASGTopLevelTargetEnvironment) -> None:
        self.parentBuilder: ASGBuilderWithGVN = parentBuilder
        self.topLevelEnvironment = topLevelEnvironment
        self.builtNodes = {}
        self.currentPredecessor = None

    def topLevelIdentifier(self, name: str):
        if self.parentBuilder is not None:
            return self.parentBuilder.topLevelIdentifier(name)

        value = self.topLevelEnvironment.lookLastBindingOf(name)
        return self.unifyWithPreviousBuiltNode(value)

    def unifyWithPreviousBuiltNode(self, node: ASGNode):
        if node is None:
            return None
        
        if not node.isPureDataNode():
            return node
        
        comparisonNode = ASGUnificationComparisonNode(node)
        unifiedNode = self.unifyChildNode(comparisonNode)
        if unifiedNode is not None:
            return ASGUnifiedNodeValue(unifiedNode.node, ASGNodeUnificationDerivation(node, unifiedNode.node))
        
        self.builtNodes[comparisonNode] = comparisonNode
        return node
    
    def unifyChildNode(self, node: ASGNode):
        unified = self.builtNodes.get(node, None)
        if unified is not None:
            return unified

        if self.parentBuilder is not None:
            return self.parentBuilder.unifyChildNode(node)
        return None
    
    def updatePredecessorWith(self, node: ASGNode):
        if node.asASGNode().isSequencingNode():
            self.currentPredecessor = node
        return node

    def build(self, kind, *arguments, **kwArguments) -> ASGNode | ASGUnifiedNodeValue:
        builtNode = kind(*arguments, **kwArguments)
        return self.updatePredecessorWith(self.unifyWithPreviousBuiltNode(builtNode))
    
    def forSyntaxExpansionBuild(self, expansionAlgorithm, syntaxNode, kind, *arguments, **kwArguments):
        return self.build(kind, ASGNodeSyntaxExpansionDerivation(expansionAlgorithm, syntaxNode), *arguments, **kwArguments)

    def forSyntaxExpansionBuildAndSequenceWith(self, expansionAlgorithm, syntaxNode, kind, predecessor, *arguments, **kwArguments):
        return self.forSyntaxExpansionSequence(expansionAlgorithm, syntaxNode, predecessor, self.forSyntaxExpansionBuild(expansionAlgorithm, syntaxNode, kind, *arguments, **kwArguments))

    def forSyntaxExpansionBuildAndSequence(self, expansionAlgorithm, syntaxNode, kind, *arguments, **kwArguments):
        lastPredecessor = self.currentPredecessor
        return self.updatePredecessorWith(self.forSyntaxExpansionBuildAndSequenceWith(expansionAlgorithm, syntaxNode, kind, lastPredecessor, *arguments, **kwArguments))

    def forSyntaxExpansionSequence(self, expansionAlgorithm, syntaxNode, predecessor, valueOrSequenceNode):
        if predecessor is None:
            if valueOrSequenceNode.isSequencingNode():
                return valueOrSequenceNode
        else:
            if valueOrSequenceNode.hasSequencingPredecessorOf(predecessor):
                return valueOrSequenceNode
            elif predecessor.isSequencingNodeForExpression(valueOrSequenceNode):
                return predecessor
        return self.forSyntaxExpansionBuild(expansionAlgorithm, syntaxNode, ASGSequenceExpressionNode, valueOrSequenceNode, predecessor = predecessor)

class ASGBetaSubstitutionContext:
    def __init__(self) -> None:
        self.substitutionTable = {}

    def setSubstitutionForNode(self, oldNode: ASGNode, replacedNode: ASGNode):
        self.substitutionTable[oldNode] = replacedNode

    def isEmpty(self) -> bool:
        return len(self.substitutionTable) == 0

class ASGBetaSubstitutionAlgorithm(ASGDynamicProgrammingAlgorithm):
    def __init__(self, substitutionContext: ASGBetaSubstitutionContext, builder: ASGBuilderWithGVN) -> None:
        super().__init__()
        self.substitutionContext = substitutionContext
        self.builder = builder

    def expandNode(self, node: ASGNode):
        if self.substitutionContext.isEmpty():
            return node
        if len(node.betaReplaceableDependencies()) == 0:
            return node
        return self(node)

class ASGExpandAndTypecheckingAlgorithm(ASGDynamicProgrammingAlgorithm):
    def __init__(self, environment: ASGEnvironment, builder: ASGBuilderWithGVN = None) -> None:
        super().__init__()
        self.environment = environment
        self.builder = builder
        if self.builder is None:
            self.builder = ASGBuilderWithGVN(None, self.environment.getTopLevelTargetEnvironment())

    def withFunctionalAnalysisEnvironment(self, newEnvironment: ASGFunctionalAnalysisEnvironment):
        return ASGExpandAndTypecheckingAlgorithm(newEnvironment, ASGBuilderWithGVN(self.builder, newEnvironment.getTopLevelTargetEnvironment()))

    def syntaxPredecessorOf(self, node: ASGSyntaxNode):
        predecessor = node.syntacticPredecessor
        if predecessor is not None:
            return self(predecessor)
        else:
            return None
        
    def makeErrorAtNode(self, message: str, node: ASGNode) -> ASGTypecheckedNode:
        type = self.builder.topLevelIdentifier('Abort')
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGErrorNode, type, message)
    
    def analyzeNodeWithExpectedType(self, node: ASGNode, expectedType: ASGNode) -> ASGTypecheckedNode:
        analyzedNode = self(node).asASGDataNode()
        if expectedType is None:
            return analyzedNode, True

        analyzedNodeType = analyzedNode.getTypeInEnvironment(self.environment)
        if analyzedNodeType.unificationEquals(expectedType.asASGTypeNode()):
            return analyzedNode, True
        return self.makeErrorAtNode('Type checking failure. Expected %s instead of %s.' % (str(expectedType), str(analyzedNodeType)), node), False
    
    def evaluateOptionalSymbol(self, node: ASGNode) -> str:
        if node is None:
            return None

        typecheckedNode, typechecked = self.analyzeNodeWithExpectedType(node, self.builder.topLevelIdentifier('Symbol'))
        if not typechecked:
            return None
        
        typecheckedNode = typecheckedNode.asASGDataNode()
        if typecheckedNode.isTypedLiteralNode():
            return typecheckedNode.value

        self.makeErrorAtNode('Expected a literal symbol.', node)
        return None
    
    def analyzeArgumentNode(self, functionalAnalyzer, node: ASGNode, index: int) -> ASGArgumentNode:
        if not node.isKindOf(ASGSyntaxBindableNameNode):
            return self.makeErrorAtNode('Expected a bindable name node for defining the argument.', node)
        
        # The first argument name and types are in the context of the parent.
        argumentAnalyzer = self
        if index != 0:
            argumentAnalyzer = functionalAnalyzer

        bindableName: ASGSyntaxBindableNameNode = node
        type = argumentAnalyzer.analyzeOptionalTypeExpression(bindableName.typeExpression)
        if type is None:
            type = argumentAnalyzer.builder.topLevelIdentifier('Any')

        name = argumentAnalyzer.evaluateOptionalSymbol(bindableName.nameExpression)
        return functionalAnalyzer.builder.forSyntaxExpansionBuild(functionalAnalyzer, node, ASGArgumentNode, type, index, name, isImplicit = bindableName.isImplicit).asASGDataNode()

    def analyzeTypeExpression(self, node: ASGNode) -> ASGTypecheckedNode:
        analyzedNode = self(node).asASGTypeNode()
        if analyzedNode.isTypeNode():
            return analyzedNode

        return self.makeErrorAtNode('Expected a type expression.', node)

    def analyzeOptionalTypeExpression(self, node: ASGNode) -> ASGTypecheckedNode:
        if node is None:
            return None
        return self.analyzeTypeExpression(node)
    
    def expandMacrosOnly(self, node: ASGNode) -> ASGNode:
        # TODO: Implement this properly.
        return node

    @asgPatternMatchingOnNodeKind(ASGSyntaxErrorNode)
    def expandSyntaxErrorNode(self, node: ASGSyntaxErrorNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        return self.makeErrorAtNode(node.message, node)

    @asgPatternMatchingOnNodeKind(ASGSyntaxAssignmentNode)
    def expandSyntaxAssignmentNode(self, node: ASGSyntaxAssignmentNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        store = self.expandMacrosOnly(node.store)
        derivation = ASGNodeSyntaxExpansionDerivation(self, node)
        if store.isKindOf(ASGSyntaxFunctionalDependentTypeNode):
            functionalDependentNode: ASGSyntaxFunctionalDependentTypeNode = store
            return self.fromNodeContinueExpanding(node, ASGSyntaxFunctionNode(derivation, None, functionalDependentNode, node.value))
        elif store.isKindOf(ASGSyntaxBindableNameNode):
            bindableNameNode: ASGSyntaxBindableNameNode = store
            if bindableNameNode.typeExpression is not None and bindableNameNode.typeExpression.isKindOf(ASGSyntaxFunctionalDependentTypeNode):
                functionalDependentNode: ASGSyntaxFunctionalDependentTypeNode = bindableNameNode.typeExpression
                function = self(ASGSyntaxFunctionNode(derivation, bindableNameNode.nameExpression, functionalDependentNode, node.value, isFixpoint = bindableNameNode.hasPostTypeExpression))
                return self.fromNodeContinueExpanding(node, ASGSyntaxBindingDefinitionNode(derivation, None, bindableNameNode.nameExpression, function))
            else:
                return self.fromNodeContinueExpanding(node, ASGSyntaxBindPatternNode(derivation, bindableNameNode, node.value, allowsRebind = False))

        selector = ASGLiteralSymbolNode(self.builder.topLevelIdentifier('Symbol'), ':=')
        return self.fromNodeContinueExpanding(node, ASGSyntaxMessageSendNode(derivation, store, selector, [node.value]))

    @asgPatternMatchingOnNodeKind(ASGSyntaxBindPatternNode)
    def expandSyntaxBindPatternNode(self, node: ASGSyntaxBindPatternNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        return self.fromNodeContinueExpanding(node, node.pattern.expandPatternWithValueAt(self, node.value, node))

    @asgPatternMatchingOnNodeKind(ASGSyntaxBindingDefinitionNode)
    def expandSyntaxBindindingDefinitionNode(self, node: ASGSyntaxBindingDefinitionNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        name = self.evaluateOptionalSymbol(node.nameExpression)
        expectedType = self.analyzeOptionalTypeExpression(node.typeExpression)
        value, typechecked = self.analyzeNodeWithExpectedType(node.valueExpression, expectedType)
        value = value.asASGDataNode()
        if name is None:
            return value

        self.environment = self.environment.childWithSymbolBinding(name, value)
        return value

    @asgPatternMatchingOnNodeKind(ASGSyntaxFunctionalDependentTypeNode)
    def expandSyntaxFunctionalDependentTypeNode(self, node: ASGSyntaxFunctionalDependentTypeNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)

        if node.argumentPattern is None:
            return self.fromNodeContinueExpanding(node, ASGSyntaxPiNode(ASGNodeSyntaxExpansionDerivation(self, node), [], node.resultType))

        argumentNodes, isExistential, isVariadic = node.argumentPattern.parseAndUnpackArgumentsPattern()
        if isExistential:
            return self.fromNodeContinueExpanding(node, ASGSyntaxSigmaNode(ASGNodeSyntaxExpansionDerivation(self, node), argumentNodes, node.resultType, isVariadic = isVariadic))
        else:
            return self.fromNodeContinueExpanding(node, ASGSyntaxPiNode(ASGNodeSyntaxExpansionDerivation(self, node), argumentNodes, node.resultType, isVariadic = isVariadic))

    @asgPatternMatchingOnNodeKind(ASGSyntaxFunctionNode)
    def expandSyntaxFunctionNode(self, node: ASGSyntaxFunctionNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        functionalType = self.expandMacrosOnly(node.functionalType)
        if not functionalType.isKindOf(ASGSyntaxFunctionalDependentTypeNode):
            return self.makeErrorAtNode(functionalType, 'Expected a functional dependent type.')
        
        return self.fromNodeContinueExpanding(node, functionalType.constructLambdaWithBody(ASGNodeSyntaxExpansionDerivation(self, node), node.nameExpression, node.body, node.isFixpoint))

    @asgPatternMatchingOnNodeKind(ASGSyntaxLambdaNode)
    def expandSyntaxLambdaNode(self, node: ASGSyntaxLambdaNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        functionalEnvironment = ASGFunctionalAnalysisEnvironment(self.environment, node.sourceDerivation.getSourcePosition())
        functionalAnalyzer = self.withFunctionalAnalysisEnvironment(functionalEnvironment)
        typedArguments = []
        arguments = node.arguments
        for i in range(len(arguments)):
            argument = arguments[i]
            typedArgument = self.analyzeArgumentNode(functionalAnalyzer, argument, i)
            if typedArgument.isKindOf(ASGArgumentNode):
                functionalEnvironment.addArgumentBinding(typedArgument)
                typedArguments.append(typedArgument)
        functionalAnalyzer.builder.currentPredecessor = None

        resultType = functionalAnalyzer.analyzeTypeExpression(node.resultType)
        piType = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGPiNode, typedArguments, resultType, isVariadic = node.isVariadic, callingConvention = node.callingConvention)

        functionalAnalyzer.builder.currentPredecessor = None
        entryPoint = functionalAnalyzer.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGEntryPointNode)

        body, bodyTypechecked = functionalAnalyzer.analyzeNodeWithExpectedType(node.body, resultType)
        if not bodyTypechecked:
            return body

        bodyExitPoint = functionalAnalyzer.builder.forSyntaxExpansionBuild(functionalAnalyzer, node, ASGExitPointNode, body, predecessor = functionalAnalyzer.builder.currentPredecessor)
        exitPoints = [bodyExitPoint]
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLambdaNode, piType, typedArguments, entryPoint, exitPoints, callingConvention = node.callingConvention)
    
    def expandTopLevelScript(self, node: ASGNode) -> ASGTopLevelScriptNode:
        entryPoint = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGEntryPointNode)
        scriptResult = self(node)
        exitPoint = self.builder.forSyntaxExpansionBuild(self, node, ASGExitPointNode, scriptResult, predecessor = self.builder.currentPredecessor)
        exitPoints = [exitPoint]
        resultType = scriptResult.getTypeInEnvironment(self.builder)
        return self.builder.forSyntaxExpansionBuild(self, node, ASGTopLevelScriptNode, resultType, entryPoint, exitPoints)

    @asgPatternMatchingOnNodeKind(ASGSyntaxPiNode)
    def expandSyntaxPiNode(self, node: ASGSyntaxPiNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        functionalEnvironment = ASGFunctionalAnalysisEnvironment(self.environment, node.sourceDerivation.getSourcePosition())
        functionalAnalyzer = self.withFunctionalAnalysisEnvironment(functionalEnvironment)
        typedArguments = []
        arguments = node.arguments
        for i in range(len(arguments)):
            argument = arguments[i]
            typedArgument = self.analyzeArgumentNode(functionalAnalyzer, argument, i)
            if typedArgument.isKindOf(ASGArgumentNode):
                functionalEnvironment.addArgumentBinding(typedArgument)
                typedArguments.append(typedArgument)
        functionalAnalyzer.builder.currentPredecessor = None

        resultType = functionalAnalyzer.analyzeTypeExpression(node.resultType)
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGPiNode, typedArguments, resultType, isVariadic = node.isVariadic, callingConvention = node.callingConvention)

    @asgPatternMatchingOnNodeKind(ASGSyntaxLiteralIntegerNode)
    def expandSyntaxLiteralIntegerNode(self, node: ASGSyntaxLiteralIntegerNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        type = self.builder.topLevelIdentifier('Integer')
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralIntegerNode, type, node.value)

    @asgPatternMatchingOnNodeKind(ASGSyntaxLiteralSymbolNode)
    def expandSyntaxLiteralSymbolNode(self, node: ASGSyntaxLiteralSymbolNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        type = self.builder.topLevelIdentifier('Symbol')
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralSymbolNode, type, node.value)

    @asgPatternMatchingOnNodeKind(ASGSyntaxIdentifierReferenceNode)
    def expandSyntaxIdentifierReferenceNode(self, node: ASGSyntaxIdentifierReferenceNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        lookupResult = self.environment.lookSymbolBindingListRecursively(node.value)
        if len(lookupResult) == 0:
            return self.makeErrorAtNode('Failed to finding binding for symbol %s.' % node.value, node)
        elif len(lookupResult) == 1:
            return self.builder.forSyntaxExpansionSequence(self, node, self.builder.currentPredecessor, self(lookupResult[0]))
        else:
            ## Potentially overloaded
            assert False

    @asgPatternMatchingOnNodeKind(ASGSyntaxApplicationNode)
    def expandSyntaxApplicationNode(self, node: ASGSyntaxApplicationNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        functional = self(node.functional)
        functionalType = functional.getTypeInEnvironment(self.environment)
        return functionalType.expandSyntaxApplicationNode(self, node)

    def expandDependentApplicationWithType(self, node: ASGSyntaxApplicationNode, dependentType: ASGPiNode):
        self.syntaxPredecessorOf(node)

        substitutionAlgorithm = ASGBetaSubstitutionAlgorithm(ASGBetaSubstitutionContext(), self.builder)
        requiredArgumentCount = len(dependentType.arguments)
        availableArgumentCount = len(node.arguments)

        # Analyze the functional.
        functional = self(node.functional)

        # Analyze the direct checkeable arguments.
        directCheckeableArgumentCount = min(requiredArgumentCount, availableArgumentCount)
        expectedType = None
        analyzedArguments = []
        for i in range(directCheckeableArgumentCount):
            argumentValue: ASGNode = node.arguments[i]
            argumentSpecification: ASGArgumentNode = dependentType.arguments[i]
            expectedType = substitutionAlgorithm.expandNode(argumentSpecification.type)
            analyzedArgument, typechecked = self.analyzeNodeWithExpectedType(argumentValue, expectedType)
            analyzedArguments.append(analyzedArgument)
            substitutionAlgorithm.substitutionContext.setSubstitutionForNode(argumentSpecification, analyzedArgument)

        # Analyze the remaining arguments
        if not dependentType.isVariadic:
            expectedType = None
        
        for i in range(availableArgumentCount):
            analyzedArgument, typechecked = self.analyzeNodeWithExpectedType(argumentValue, expectedType)
            analyzedArguments.append(analyzedArgument)

        # Analyze the result type.
        resultType = substitutionAlgorithm.expandNode(dependentType.resultType)

        # Make the application node
        application = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGApplicationNode, resultType, functional, analyzedArguments)

        # Check the argument sizes.
        if requiredArgumentCount != availableArgumentCount:
            if not dependentType.isVariadic:
                return self.makeErrorAtNode(node, 'Application argument count mismatch. Got %d instead of %d arguments.' % (availableArgumentCount, requiredArgumentCount))
            elif availableArgumentCount < requiredArgumentCount: 
                return self.makeErrorAtNode(node, 'Required at least %d arguments for variadic application.' % requiredArgumentCount)
        
        return application

    @asgPatternMatchingOnNodeKind(ASGSyntaxSequenceNode)
    def expandSyntaxSequenceNode(self, node: ASGSyntaxSequenceNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        if len(node.elements) == 0:
            type = self.builder.topLevelIdentifier('Void')
            return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralUnitNode, type)

        elementsToExpand = node.elements
        for i in range(len(elementsToExpand)):
            if i + 1 < len(elementsToExpand):
                self(elementsToExpand[i])
            else:
                return self.fromNodeContinueExpanding(node, elementsToExpand[i])
        assert False, "Should not reach here."
    
    @asgPatternMatchingOnNodeKind(ASGSyntaxTupleNode)
    def expandSyntaxTupleNode(self, node: ASGSyntaxTupleNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        if len(node.elements) == 0:
            type = self.builder.topLevelIdentifier('Void')
            return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralUnitNode, type)
        
        elements = []
        for element in node.elements:
            expandedElement = self(element)
            elements.append(expandedElement)

        # If there are all elements, then this is a product type formation node
        if all(element.isTypeNode() for element in elements):
            return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGProductTypeNode, elements)

        elementTypes = list(map(lambda n: n.asASGDataNode().getTypeInEnvironment(self.environment), elements))
        type = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGProductTypeNode, elementTypes)
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGTupleNode, type, elements)
    
    @asgPatternMatchingOnNodeKind(ASGTypecheckedNode)
    def expandSyntaxTypecheckedNode(self, node: ASGTypecheckedNode) -> ASGTypecheckedNode:
        return node

def asgExpandAndTypecheck(environment: ASGEnvironment, node: ASGNode):
    expander = ASGExpandAndTypecheckingAlgorithm(environment)
    result = expander.expandTopLevelScript(node)
    return result

def asgMakeScriptAnalysisEnvironment(target: CompilationTarget, sourcePosition: SourcePosition, scriptPath: str) -> ASGEnvironment:
    topLevelEnvironment = ASGTopLevelTargetEnvironment.getForTarget(target)
    scriptDirectory = os.path.dirname(scriptPath)
    scriptName = os.path.basename(scriptPath)
    return ASGScriptEnvironment(topLevelEnvironment, sourcePosition, scriptDirectory, scriptName)
