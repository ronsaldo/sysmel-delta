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

    def isSourceDerivationAttribute(self) -> bool:
        return False
    
    def isDataAttribute(self) -> bool:
        return False

    def isDataInputPort(self) -> bool:
        return False

class ASGNodeConstructionAttribute(ASGNodeAttributeDescriptor):
    def isConstructionAttribute(self) -> bool:
        return True

    def initializeWithConstructorValueOn(self, constructorValue, instance) -> bool:
        self.storeValueIn(constructorValue, instance)

class ASGNodeDataAttribute(ASGNodeConstructionAttribute):
    def __init__(self, type) -> None:
        super().__init__()
        self.type = type

    def isDataAttribute(self) -> bool:
        return True

class ASGNodeSourceDerivationAttribute(ASGNodeConstructionAttribute):
    def isConstructionAttribute(self) -> bool:
        return True

    def isSpecialAttribute(self) -> bool:
        return True

    def isSourceDerivationAttribute(self) -> bool:
        return True
    
class ASGNodeDataInputPort(ASGNodeConstructionAttribute):
    def isConstructionAttribute(self) -> bool:
        return True

    def isDataInputPort(self) -> bool:
        return True

class ASGNodeOptionalDataInputPort(ASGNodeConstructionAttribute):
    def isConstructionAttribute(self) -> bool:
        return True

    def isDataInputPort(self) -> bool:
        return True

class ASGNodeDataInputPorts(ASGNodeConstructionAttribute):
    def isConstructionAttribute(self) -> bool:
        return True

    def isDataInputPort(self) -> bool:
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
        constructionAttributes: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isConstructionAttribute(), descriptors))
        dataAttributes: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isDataAttribute(), descriptors))
        dataInputPorts: list[ASGNodeAttributeDescriptor] = list(filter(lambda desc: desc.isDataInputPort(), descriptors))

        constructionAttributeDictionary = {}
        for attr in constructionAttributes:
            constructionAttributeDictionary[attr.name] = attr
            
        nodeClass = super().__new__(cls, name, bases, attributes)
        nodeClass.__asgAttributeDescriptors__ = descriptors
        nodeClass.__asgSpecialAttributes__ = specialAttributes
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

class ASGErrorNode(ASGNode):
    message = ASGNodeDataAttribute(int)
    innerNodes = ASGNodeDataInputPorts()

class ASGAtomicValueNode(ASGNode):
    pass

class ASGAtomicCharacterValueNode(ASGAtomicValueNode):
    value = ASGNodeDataAttribute(int)

class ASGAtomicIntegerValueNode(ASGAtomicValueNode):
    value = ASGNodeDataAttribute(int)

class ASGAtomicFloatValueNode(ASGAtomicValueNode):
    value = ASGNodeDataAttribute(float)

class ASGAtomicStringValueNode(ASGAtomicValueNode):
    value = ASGNodeDataAttribute(str)

class ASGAtomicSymbolValueNode(ASGAtomicValueNode):
    value = ASGNodeDataAttribute(str)

class ASGApplicationNode(ASGNode):
    functional = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()
    kind = ASGNodeDataAttribute(int)

class ASGAssignmentNode(ASGNode):
    store = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()

class ASGBindableNameNode(ASGNode):
    typeExpression = ASGNodeDataInputPort()
    nameExpression = ASGNodeDataInputPort()
    isImplicit = ASGNodeDataAttribute(bool)
    isExistential = ASGNodeDataAttribute(bool)
    isVariadic = ASGNodeDataAttribute(bool)
    isMutable = ASGNodeDataAttribute(bool)
    hasPostTypeExpression = ASGNodeDataAttribute(bool)

class ASGBindPatternNode(ASGNode):
    pattern = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()

class ASGBinaryExpressionSequenceNode(ASGNode):
    elements = ASGNodeDataInputPorts()

class ASGBlockNode(ASGNode):
    functionType = ASGNodeDataInputPort()
    body = ASGNodeDataInputPorts()

class ASGIdentifierReferenceNode(ASGNode):
    value = ASGNodeDataAttribute(str)

class ASGLexicalBlockNode(ASGNode):
    body = ASGNodeDataInputPorts()

class ASGMessageSendNode(ASGNode):
    receiver = ASGNodeOptionalDataInputPort()
    selector = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()

class ASGDictionaryNode(ASGNode):
    elements = ASGNodeDataInputPorts()

class ASGFunctionalDependentTypeNode(ASGNode):
    argumentPattern = ASGNodeOptionalDataInputPort()
    resultType = ASGNodeOptionalDataInputPort()

class ASGSequenceNode(ASGNode):
    elements = ASGNodeDataInputPorts()

class ASGTupleNode(ASGNode):
    elements = ASGNodeDataInputPorts()

class ASGParseTreeFrontEnd(ParseTreeVisitor):
    def visitErrorNode(self, node: ParseTreeErrorNode):
        return ASGErrorNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.message, self.transformNodes(node.innerNodes))

    def visitApplicationNode(self, node: ParseTreeApplicationNode):
        return ASGApplicationNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functional), self.transformNodes(node.arguments), node.kind)

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        return ASGAssignmentNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.store), self.visitNode(node.value))

    def visitBindPatternNode(self, node: ParseTreeBindPatternNode):
        return ASGBindPatternNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.pattern), self.visitNode(node.value))

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        return ASGBinaryExpressionSequenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements))

    def visitBindableNameNode(self, node: ParseTreeBindableNameNode):
        return ASGBindableNameNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.typeExpression), self.visitOptionalNode(node.nameExpression), node.isImplicit, node.isExistential, node.isVariadic, node.isMutable, node.hasPostTypeExpression)

    def visitBlockNode(self, node: ParseTreeBlockNode):
        return ASGBlockNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functionType), self.visitNode(node.body))

    def visitDictionaryNode(self, node: ParseTreeDictionaryNode):
        return ASGDictionaryNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements))

    def visitFunctionalDependentTypeNode(self, node: ParseTreeFunctionalDependentTypeNode):
        return ASGFunctionalDependentTypeNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.argumentPattern), self.visitOptionalNode(node.resultType))

    def visitIdentifierReferenceNode(self, node: ParseTreeIdentifierReferenceNode):
        return ASGIdentifierReferenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value)

    def visitLexicalBlockNode(self, node: ParseTreeLexicalBlockNode):
        return ASGLexicalBlockNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.body))

    def visitLiteralCharacterNode(self, node: ParseTreeLiteralCharacterNode):
        return ASGAtomicCharacterValueNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value)

    def visitLiteralFloatNode(self, node: ParseTreeLiteralFloatNode):
        return ASGAtomicFloatValueNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value)

    def visitLiteralIntegerNode(self, node: ParseTreeLiteralIntegerNode):
        return ASGAtomicIntegerValueNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value)

    def visitLiteralSymbolNode(self, node: ParseTreeLiteralSymbolNode):
        return ASGAtomicSymbolValueNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value)

    def visitLiteralStringNode(self, node: ParseTreeLiteralStringNode):
        return ASGAtomicStringValueNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value)

    def visitMessageSendNode(self, node: ParseTreeMessageSendNode):
        return ASGMessageSendNode(ASGNodeSourceCodeDerivation, self.visitOptionalNode(node.receiver), self.visitNode(node.selector), self.transformNodes(node.arguments))

    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        return ASGSequenceNode(ASGNodeSourceCodeDerivation, self.transformNodes(node.elements))

    def visitTupleNode(self, node: ParseTreeTupleNode):
        return ASGTupleNode(ASGNodeSourceCodeDerivation, self.transformNodes(node.elements))
