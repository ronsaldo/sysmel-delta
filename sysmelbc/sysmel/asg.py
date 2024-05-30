from abc import ABC, abstractmethod
from typing import Any
from .target import *
from .parsetree import *

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
    
    def getNodeInputsOf(self, instance):
        return []
    
    def __get__(self, instance, owner):
        return self.loadValueFrom(instance)
    
    def __set__(self, instance, value):
        raise Exception('Not supported')

class ASGNodeConstructionAttribute(ASGNodeAttributeDescriptor):
    def isConstructionAttribute(self) -> bool:
        return True

    def isNumberedConstructionAttribute(self) -> bool:
        return True

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
        if 'default' in kwArguments:
            self.hasDefaultValue = True
            self.defaultValue = kwArguments['default']

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

class ASGPredecessorAttribute(ASGNodeConstructionAttributeWithSourceDerivation):
    def isNumberedConstructionAttribute(self) -> bool:
        return False

    def initializeWithDefaultConstructorValueOn(self, instance):
        self.storeValueIn(None, instance)
        self.storeSourceDerivationIn(None, instance)

    def getNodeInputsOf(self, instance):
        value = self.loadValueFrom(instance)
        if value is None:
            return []
        return [value]
    
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
    
class ASGNodeDataInputPort(ASGNodeConstructionAttributeWithSourceDerivation):
    def initializeWithConstructorValueOn(self, constructorValue, instance):
        self.storeValueIn(constructorValue.asASGDataNode(), instance)
        self.storeSourceDerivationIn(constructorValue.asASGDataNodeDerivation(), instance)

    def isDataInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        return [self.loadValueFrom(instance)]

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
            return []
        return [value]

class ASGNodeTypeInputNode(ASGNodeConstructionAttributeWithSourceDerivation):
    def isTypeInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        return [self.loadValueFrom(instance)]
    
class ASGNodeOptionalTypeInputNode(ASGNodeConstructionAttribute):
    def isTypeInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        type = self.loadValueFrom(instance)
        if type is None:
            return []
        return [self.loadValueFrom(instance)]
    
class ASGNodeDataInputPorts(ASGNodeConstructionAttributeWithSourceDerivation):
    def initializeWithConstructorValueOn(self, constructorValue, instance) -> bool:
        self.storeValueIn(list(map(lambda x: x.asASGDataNode(), constructorValue)), instance)
        self.storeSourceDerivationIn(list(map(lambda x: x.asASGDataNodeDerivation(), constructorValue)), instance)

    def isDataInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        return self.loadValueFrom(instance)

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
        return nodeClass

class ASGNode(metaclass = ASGNodeMetaclass):
    def __init__(self, *positionalArguments, **kwArguments) -> None:
        super().__init__()

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

    def asASGNode(self):
        return self

    def asASGNodeDerivation(self):
        return ASGNodeNoDerivation.getSingleton()

    def asASGDataNode(self):
        return self.asASGNode()

    def asASGDataNodeDerivation(self):
        return self.asASGNodeDerivation()
    
    def isPureDataNode(self) -> bool:
        raise Exception("Subclass responsibility isPureDataNode")
    
    def isSequencingNode(self) -> bool:
        return False
    
    def asASGSequencingNode(self):
        if self.isPureDataNode():
            return None

        return self.asASGNode()

    def asASGSequencingNodeDerivation(self):
        if self.isPureDataNode():
            return None

        return self.asASGNodeDerivation()

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
    
    def hasSequencingPredecessorOf(self, predecessor) -> bool:
        return False
    
    def __str__(self) -> str:
        return self.printNameWithDataAttributes()

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

class ASGSyntaxBindPatternNode(ASGSyntaxNode):
    pattern = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()

class ASGSyntaxBinaryExpressionSequenceNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

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

class ASGSyntaxSequenceNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntaxTupleNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

class ASGParseTreeFrontEnd(ParseTreeVisitor):
    def __init__(self):
        self.lastVisitedNode = None

    def visitNode(self, node: ParseTreeNode):
        self.lastVisitedNode = super().visitNode(node)
        return self.lastVisitedNode

    def visitErrorNode(self, node: ParseTreeErrorNode):
        return ASGSyntaxErrorNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.message, self.transformNodes(node.innerNodes), syntacticPredecessor = self.lastVisitedNode)

    def visitApplicationNode(self, node: ParseTreeApplicationNode):
        return ASGSyntaxApplicationNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functional), self.transformNodes(node.arguments), node.kind, syntacticPredecessor = self.lastVisitedNode)

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        return ASGSyntaxAssignmentNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.store), self.visitNode(node.value), syntacticPredecessor = self.lastVisitedNode)

    def visitBindPatternNode(self, node: ParseTreeBindPatternNode):
        return ASGSyntaxBindPatternNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.pattern), self.visitNode(node.value), syntacticPredecessor = self.lastVisitedNode)

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        return ASGSyntaxBinaryExpressionSequenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitBindableNameNode(self, node: ParseTreeBindableNameNode):
        return ASGSyntaxBindableNameNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.typeExpression), self.visitOptionalNode(node.nameExpression), node.isImplicit, node.isExistential, node.isVariadic, node.isMutable, node.hasPostTypeExpression, syntacticPredecessor = self.lastVisitedNode)

    def visitBlockNode(self, node: ParseTreeBlockNode):
        return ASGSyntaxBlockNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functionType), self.visitNode(node.body), syntacticPredecessor = self.lastVisitedNode)

    def visitDictionaryNode(self, node: ParseTreeDictionaryNode):
        return ASGSyntaxDictionaryNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitFunctionalDependentTypeNode(self, node: ParseTreeFunctionalDependentTypeNode):
        return ASGSyntaxFunctionalDependentTypeNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.argumentPattern), self.visitOptionalNode(node.resultType), syntacticPredecessor = self.lastVisitedNode)

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
        return ASGSyntaxMessageSendNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.receiver), self.visitNode(node.selector), self.transformNodes(node.arguments), syntacticPredecessor = self.lastVisitedNode)

    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        return ASGSyntaxSequenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitTupleNode(self, node: ParseTreeTupleNode):
        return ASGSyntaxTupleNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

class ASGTypecheckedNode(ASGNode):
    sourceDerivation = ASGNodeSourceDerivationAttribute()

    def asASGNodeDerivation(self):
        return self.sourceDerivation

class ASGTypecheckedSequencedExpression(ASGTypecheckedNode):
    predecessor = ASGSequencingPredecessorAttribute()
    expression = ASGNodeDataInputPort()

    def isPureDataNode(self) -> bool:
        return False
    
    def asASGDataNode(self):
        return self.expression.asASGDataNode()
    
    def asASGDataNodeDerivation(self):
        return self.expression.asASGDataNodeDerivation()
    
    def isSequencingNode(self) -> bool:
        return True

    def hasSequencingPredecessorOf(self, predecessor) -> bool:
        return self.predecessor is predecessor

class ASGTypedExpressionNode(ASGTypecheckedNode):
    type = ASGNodeTypeInputNode()

class ASGTypedLiteralNode(ASGTypedExpressionNode):
    def isPureDataNode(self) -> bool:
        return True
    
class ASGTypedLiteralCharacterNode(ASGTypedLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGTypedLiteralIntegerNode(ASGTypedLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGTypedLiteralFloatNode(ASGTypedLiteralNode):
    value = ASGNodeDataAttribute(float)

class ASGTypedLiteralSymbolNode(ASGTypedLiteralNode):
    value = ASGNodeDataAttribute(str)

class ASGTypedLiteralUnitNode(ASGTypedLiteralNode):
    pass

class ASGTypeNode(ASGTypecheckedNode):
    def isPureDataNode(self) -> bool:
        return True

class ASGBaseTypeNode(ASGTypeNode):
    name = ASGNodeDataAttribute(str)

class ASGPrimitiveType(ASGBaseTypeNode):
    size = ASGNodeDataAttribute(int)
    alignment = ASGNodeDataAttribute(int)

class ASGPrimitiveIntegerType(ASGPrimitiveType):
    isSigned = ASGNodeDataAttribute(int)
    pass

class ASGPrimitiveFloat(ASGPrimitiveType):
    pass

class ASGUniverseTypeNode(ASGTypeNode):
    pass

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
        result += '  N%d [label="%s"]\n' % (nodeCount, node.printNameWithDataAttributes().replace('\\', '\\\\').replace('"', '\"'))
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

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.function(*args, **kwds)

def asgPatternMatchingOnNodeKind(kind: type):
    def makePattern(function):
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

class ASGDynamicProgrammingAlgorithm(metaclass = ASGDynamicProgrammingAlgorithmMetaclass):
    def __init__(self) -> None:
        self.processedNodes = {}

    def __call__(self, node: ASGNode) -> Any:
        if node in self.processedNodes:
            return self.processedNodes[node]

        patternKindDictionary = self.__class__.__asgDPAPatternKindDictionary__
        currentClass = node.__class__
        while currentClass is not None:
            patterns: list[ASGPatternMatchingNodeKindPattern] | None = patternKindDictionary.get(currentClass, None)
            if patterns is not None:
                for pattern in patterns:
                    if pattern.matchesNode(node):
                        result = pattern(self, node)
                        self.processedNodes[node] = result
                        return result

            if len(currentClass.__bases__) != 0:
                currentClass = currentClass.__bases__[0]
            else:
                currentClass = None
        raise Exception("Failed to find matching pattern for %s in %s." % (str(node), str(self)))

class ASGEnvironment(ABC):
    @abstractmethod
    def getTopLevelTargetEnvironment(self):
        pass

    def isLexicalEnvironment(self):
        return False

    def isScriptEnvironment(self):
        return False

class ASGTopLevelTargetEnvironment(ASGEnvironment):
    def __init__(self, target: CompilationTarget) -> None:
        super().__init__()
        self.target = target
        self.symbolTable = {}
        topLevelDerivation = ASGNodeNoDerivation.getSingleton()
        self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'Integer'))
        self.addBaseType(ASGBaseTypeNode(topLevelDerivation, 'Void'))

    def addBaseType(self, baseType: ASGBaseTypeNode):
        self.addSymbolValue(baseType.name, baseType)

    def addSymbolValue(self, name: str, value: ASGNode):
        if name not in self.symbolTable:
            self.symbolTable[name] = []
        self.symbolTable[name].append(value)

    def lookLastBindingOf(self, name: str):
        if not name in self.symbolTable:
            return None
        return self.symbolTable[name][-1]

    def getTopLevelTargetEnvironment(self):
        return self
    
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

class ASGLexicalEnvironment(ASGChildEnvironment):
    def isLexicalEnvironment(self):
        return True

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

    def topLevelIdentifier(self, name: str):
        if self.parentBuilder is not None:
            return self.parentBuilder.topLevelIdentifier(name)

        value = self.topLevelEnvironment.lookLastBindingOf(name)
        return self.unifyWithPreviousBuiltNode(value)

    def unifyWithPreviousBuiltNode(self, node: ASGNode):
        return node

    def build(self, kind, *arguments, **kwArguments) -> ASGNode | ASGUnifiedNodeValue:
        builtNode = kind(*arguments, **kwArguments)
        return self.unifyWithPreviousBuiltNode(builtNode)
    
    def forSyntaxExpansionBuild(self, expansionAlgorithm, syntaxNode, kind, *arguments, **kwArguments):
        return self.build(kind, ASGNodeSyntaxExpansionDerivation(expansionAlgorithm, syntaxNode), *arguments, **kwArguments)

    def forSyntaxExpansionBuildAndSequence(self, expansionAlgorithm, syntaxNode, kind, predecessor, *arguments, **kwArguments):
        return self.forSyntaxExpansionSequence(expansionAlgorithm, syntaxNode, predecessor, self.forSyntaxExpansionBuild(expansionAlgorithm, syntaxNode, kind, *arguments, **kwArguments))

    def forSyntaxExpansionSequence(self, expansionAlgorithm, syntaxNode, predecessor, valueOrSequenceNode):
        if predecessor is None:
            if valueOrSequenceNode.isSequencingNode():
                return valueOrSequenceNode
        else:
            if valueOrSequenceNode is predecessor:
                return valueOrSequenceNode
            if valueOrSequenceNode.hasSequencingPredecessorOf(predecessor):
                return valueOrSequenceNode
        return self.forSyntaxExpansionBuild(expansionAlgorithm, syntaxNode, ASGTypecheckedSequencedExpression, valueOrSequenceNode, predecessor = predecessor)
    
class ASGExpandAndTypecheckingAlgorithm(ASGDynamicProgrammingAlgorithm):
    def __init__(self, environment: ASGEnvironment) -> None:
        super().__init__()
        self.environment = environment
        self.builder = ASGBuilderWithGVN(None, self.environment.getTopLevelTargetEnvironment())

    def syntaxPredecessorOf(self, node: ASGSyntaxNode):
        predecessor = node.syntacticPredecessor
        if predecessor is not None:
            return self(predecessor)
        else:
            return None

    @asgPatternMatchingOnNodeKind(ASGSyntaxLiteralIntegerNode)
    def expandLiteralIntegerNode(self, node: ASGSyntaxLiteralIntegerNode) -> tuple[ASGTypecheckedNode, ASGTypecheckedNode]:
        predecessor = self.syntaxPredecessorOf(node)
        type = self.builder.topLevelIdentifier('Integer')
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGTypedLiteralIntegerNode, predecessor, type, node.value)

    @asgPatternMatchingOnNodeKind(ASGSyntaxSequenceNode)
    def expandSequenceNode(self, node: ASGSyntaxSequenceNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        if len(node.elements) == 0:
            type = self.builder.topLevelIdentifier('Void')
            return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGTypedLiteralUnitNode, predecessor, type)

        result = None
        for element in node.elements:
            result = self(element)
            predecessor = result
        return result

def asgExpandAndTypecheck(environment: ASGEnvironment, node: ASGNode):
    expander = ASGExpandAndTypecheckingAlgorithm(environment)
    result = expander(node)
    return result

def asgMakeScriptAnalysisEnvironment(target: CompilationTarget, sourcePosition: SourcePosition, scriptPath: str) -> ASGEnvironment:
    topLevelEnvironment = ASGTopLevelTargetEnvironment.getForTarget(target)
    scriptDirectory = os.path.dirname(scriptPath)
    scriptName = os.path.basename(scriptPath)
    return ASGScriptEnvironment(topLevelEnvironment, sourcePosition, scriptDirectory, scriptName)
