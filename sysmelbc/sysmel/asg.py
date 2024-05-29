from abc import ABC, abstractmethod
from .parsetree import *

class ASGNodeDerivation(ABC):
    pass

class ASGNodeSourceCodeDerivation(ASGNodeDerivation):
    def __init__(self, sourcePosition: SourcePosition) -> None:
        super().__init__()
        self.sourcePosition = sourcePosition

class ASGNodeNoDerivation(ASGNodeDerivation):
    pass

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

    def isSyntacticPredecessorAttribute(self) -> bool:
        return False
    
    def isSourceDerivationAttribute(self) -> bool:
        return False
    
    def isDataAttribute(self) -> bool:
        return False

    def isDataInputPort(self) -> bool:
        return False
    
    def getNodeInputsOf(self, instance):
        return []

class ASGNodeConstructionAttribute(ASGNodeAttributeDescriptor):
    def isConstructionAttribute(self) -> bool:
        return True

    def isNumberedConstructionAttribute(self) -> bool:
        return True

    def initializeWithConstructorValueOn(self, constructorValue, instance) -> bool:
        self.storeValueIn(constructorValue, instance)

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

class ASGSyntacticPredecessorAttribute(ASGNodeConstructionAttribute):
    def isSyntacticPredecessorAttribute(self) -> bool:
        return True

    def isNumberedConstructionAttribute(self) -> bool:
        return False

    def initializeWithDefaultConstructorValueOn(self, instance):
        self.storeValueIn(None, instance)

    def getNodeInputsOf(self, instance):
        value = self.loadValueFrom(instance)
        if value is None:
            return []
        return [value]

class ASGNodeDataInputPort(ASGNodeConstructionAttribute):
    def isDataInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        return [self.loadValueFrom(instance)]

class ASGNodeOptionalDataInputPort(ASGNodeConstructionAttribute):
    def isDataInputPort(self) -> bool:
        return True

    def getNodeInputsOf(self, instance):
        value =  self.loadValueFrom(instance)
        if value is None:
            return []
        return [value]

class ASGNodeDataInputPorts(ASGNodeConstructionAttribute):
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
        dataAttributes: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isDataAttribute(), descriptors))
        dataInputPorts: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isDataInputPort(), descriptors))

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
        nodeClass.__asgConstructionAttributes__ = constructionAttributes
        nodeClass.__asgConstructionAttributeDictionary__ = constructionAttributeDictionary
        nodeClass.__asgDataAttributes__ = dataAttributes
        nodeClass.__asgDataInputPorts__ = dataInputPorts
        return nodeClass

class ASGNode(metaclass = ASGNodeMetaclass):
    sourceDerivation = ASGNodeSourceDerivationAttribute()

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

    def allDependencies(self):
        for dependency in self.syntacticDependencies():
            yield dependency
        for dependency in self.effectDependencies():
            yield dependency
        for dependency in self.dataDependencies():
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
    
    def __str__(self) -> str:
        return self.printNameWithDataAttributes()

class ASGSyntacticalNode(ASGNode):
    syntacticPredecessor = ASGSyntacticPredecessorAttribute()

class ASGSyntacticalErrorNode(ASGSyntacticalNode):
    message = ASGNodeDataAttribute(int)
    innerNodes = ASGNodeDataInputPorts()

class ASGSyntacticalLiteralNode(ASGSyntacticalNode):
    pass

class ASGSyntacticalLiteralCharacterNode(ASGSyntacticalLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGSyntacticalLiteralIntegerNode(ASGSyntacticalLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGSyntacticalLiteralFloatNode(ASGSyntacticalLiteralNode):
    value = ASGNodeDataAttribute(float)

class ASGSyntacticalLiteralStringNode(ASGSyntacticalLiteralNode):
    value = ASGNodeDataAttribute(str)

class ASGSyntacticalLiteralSymbolNode(ASGSyntacticalLiteralNode):
    value = ASGNodeDataAttribute(str)

class ASGSyntacticalApplicationNode(ASGSyntacticalNode):
    functional = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()
    kind = ASGNodeDataAttribute(int, default = 0)

class ASGSyntacticalAssignmentNode(ASGSyntacticalNode):
    store = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()

class ASGSyntacticalBindableNameNode(ASGSyntacticalNode):
    typeExpression = ASGNodeOptionalDataInputPort()
    nameExpression = ASGNodeOptionalDataInputPort()
    isImplicit = ASGNodeDataAttribute(bool, default = False)
    isExistential = ASGNodeDataAttribute(bool, default = False)
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    isMutable = ASGNodeDataAttribute(bool, default = False)
    hasPostTypeExpression = ASGNodeDataAttribute(bool, default = False)

class ASGSyntacticalBindPatternNode(ASGSyntacticalNode):
    pattern = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()

class ASGSyntacticalBinaryExpressionSequenceNode(ASGSyntacticalNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntacticalBlockNode(ASGSyntacticalNode):
    functionType = ASGNodeDataInputPort()
    body = ASGNodeDataInputPorts()

class ASGSyntacticalIdentifierReferenceNode(ASGSyntacticalNode):
    value = ASGNodeDataAttribute(str)

class ASGSyntacticalLexicalBlockNode(ASGSyntacticalNode):
    body = ASGNodeDataInputPort()

class ASGSyntacticalMessageSendNode(ASGSyntacticalNode):
    receiver = ASGNodeOptionalDataInputPort()
    selector = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()

class ASGSyntacticalDictionaryNode(ASGSyntacticalNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntacticalFunctionalDependentTypeNode(ASGSyntacticalNode):
    argumentPattern = ASGNodeOptionalDataInputPort()
    resultType = ASGNodeOptionalDataInputPort()

class ASGSyntacticalSequenceNode(ASGSyntacticalNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntacticalTupleNode(ASGSyntacticalNode):
    elements = ASGNodeDataInputPorts()

class ASGParseTreeFrontEnd(ParseTreeVisitor):
    def __init__(self):
        self.lastVisitedNode = None

    def visitNode(self, node: ParseTreeNode):
        self.lastVisitedNode = super().visitNode(node)
        return self.lastVisitedNode

    def visitErrorNode(self, node: ParseTreeErrorNode):
        return ASGSyntacticalErrorNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.message, self.transformNodes(node.innerNodes), syntacticPredecessor = self.lastVisitedNode)

    def visitApplicationNode(self, node: ParseTreeApplicationNode):
        return ASGSyntacticalApplicationNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functional), self.transformNodes(node.arguments), node.kind, syntacticPredecessor = self.lastVisitedNode)

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        return ASGSyntacticalAssignmentNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.store), self.visitNode(node.value), syntacticPredecessor = self.lastVisitedNode)

    def visitBindPatternNode(self, node: ParseTreeBindPatternNode):
        return ASGSyntacticalBindPatternNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.pattern), self.visitNode(node.value), syntacticPredecessor = self.lastVisitedNode)

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        return ASGSyntacticalBinaryExpressionSequenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitBindableNameNode(self, node: ParseTreeBindableNameNode):
        return ASGSyntacticalBindableNameNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.typeExpression), self.visitOptionalNode(node.nameExpression), node.isImplicit, node.isExistential, node.isVariadic, node.isMutable, node.hasPostTypeExpression, syntacticPredecessor = self.lastVisitedNode)

    def visitBlockNode(self, node: ParseTreeBlockNode):
        return ASGSyntacticalBlockNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functionType), self.visitNode(node.body), syntacticPredecessor = self.lastVisitedNode)

    def visitDictionaryNode(self, node: ParseTreeDictionaryNode):
        return ASGSyntacticalDictionaryNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitFunctionalDependentTypeNode(self, node: ParseTreeFunctionalDependentTypeNode):
        return ASGSyntacticalFunctionalDependentTypeNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.argumentPattern), self.visitOptionalNode(node.resultType), syntacticPredecessor = self.lastVisitedNode)

    def visitIdentifierReferenceNode(self, node: ParseTreeIdentifierReferenceNode):
        return ASGSyntacticalIdentifierReferenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLexicalBlockNode(self, node: ParseTreeLexicalBlockNode):
        return ASGSyntacticalLexicalBlockNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.body), syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralCharacterNode(self, node: ParseTreeLiteralCharacterNode):
        return ASGSyntacticalLiteralCharacterNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralFloatNode(self, node: ParseTreeLiteralFloatNode):
        return ASGSyntacticalLiteralFloatNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralIntegerNode(self, node: ParseTreeLiteralIntegerNode):
        return ASGSyntacticalLiteralIntegerNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralSymbolNode(self, node: ParseTreeLiteralSymbolNode):
        return ASGSyntacticalLiteralSymbolNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralStringNode(self, node: ParseTreeLiteralStringNode):
        return ASGSyntacticalLiteralStringNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitMessageSendNode(self, node: ParseTreeMessageSendNode):
        return ASGSyntacticalMessageSendNode(ASGNodeSourceCodeDerivation, self.visitOptionalNode(node.receiver), self.visitNode(node.selector), self.transformNodes(node.arguments), syntacticPredecessor = self.lastVisitedNode)

    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        return ASGSyntacticalSequenceNode(ASGNodeSourceCodeDerivation, self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitTupleNode(self, node: ParseTreeTupleNode):
        return ASGSyntacticalTupleNode(ASGNodeSourceCodeDerivation, self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

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
        for dependency in node.syntacticDependencies():
            dependencyName = nodeToNameDictionary[dependency]
            result += '  %s -> %s [color = brown]\n' % (nodeName, dependencyName)
        for dependency in node.effectDependencies():
            dependencyName = nodeToNameDictionary[dependency]
            result += '  %s -> %s [color = blue]\n' % (nodeName, dependencyName)
        for dependency in node.dataDependencies():
            dependencyName = nodeToNameDictionary[dependency]
            result += '  %s -> %s [color = green]\n' % (nodeName, dependencyName)
    result += '}\n'
    return result