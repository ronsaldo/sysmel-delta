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

class ASGNodeKind:
    def __init__(self, name: str) -> None:
        pass

class ASGNode(ABC):
    def __init__(self, sourceDerivation: ASGNodeDerivation) -> None:
        super().__init__()
        self.sourceDerivation = sourceDerivation

class ASGErrorNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, message: str, innerNodes: list[ASGNode]) -> None:
        super().__init__(sourceDerivation)
        self.message = message
        self.innerNodes = innerNodes

class ASGAtomicValueNode(ASGNode):
    pass

class ASGAtomicCharacterValueNode(ASGAtomicValueNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, value: int) -> None:
        super().__init__(sourceDerivation)
        self.value = value

class ASGAtomicIntegerValueNode(ASGAtomicValueNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, value: int) -> None:
        super().__init__(sourceDerivation)
        self.value = value

class ASGAtomicFloatValueNode(ASGAtomicValueNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, value: float) -> None:
        super().__init__(sourceDerivation)
        self.value = value

class ASGAtomicStringValueNode(ASGAtomicValueNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, value: str) -> None:
        super().__init__(sourceDerivation)
        self.value = value

class ASGAtomicSymbolValueNode(ASGAtomicValueNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, value: str) -> None:
        super().__init__(sourceDerivation)
        self.value = value

class ASGApplicationNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, functional: ASGNode, arguments: list[ASGNode], kind: int) -> None:
        super().__init__(sourceDerivation)
        self.functional = functional
        self.arguments = arguments
        self.kind = kind

class ASGAssignmentNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, store: ASGNode, value: ASGNode) -> None:
        super().__init__(sourceDerivation)
        self.store = store
        self.value = value

class ASGBindableNameNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, typeExpression: ASGNode, nameExpression: ASGNode, isImplicit: bool, isExistential: bool, isVariadic: bool, isMutable: bool, hasPostTypeExpression: bool) -> None:
        super().__init__(sourceDerivation)
        self.typeExpression = typeExpression
        self.nameExpression = nameExpression
        self.isImplicit = isImplicit
        self.isExistential = isExistential
        self.isVariadic = isVariadic
        self.isMutable = isMutable
        self.hasPostTypeExpression = hasPostTypeExpression

class ASGBindPatternNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, pattern: ASGNode, value: ASGNode) -> None:
        super().__init__(sourceDerivation)
        self.pattern = pattern
        self.value = value

class ASGBinaryExpressionSequenceNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, elements: list[ASGNode]) -> None:
        super().__init__(sourceDerivation)
        self.elements = elements

class ASGBlockNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, functionType: ASGNode, body: ASGNode) -> None:
        super().__init__(sourceDerivation)
        self.functionType = functionType
        self.body = body

class ASGIdentifierReferenceNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, value: str) -> None:
        super().__init__(sourceDerivation)
        self.value = value

class ASGLexicalBlockNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, body: ASGNode) -> None:
        super().__init__(sourceDerivation)
        self.body = body

class ASGMessageSendNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, receiver: ASGNode | None, selector: ASGNode, arguments: list[ASGNode]) -> None:
        super().__init__(sourceDerivation)
        self.receiver = receiver
        self.selector = selector
        self.arguments = arguments

class ASGDictionaryNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, elements: list[ASGNode]) -> None:
        super().__init__(sourceDerivation)
        self.elements = elements

class ASGFunctionalDependentTypeNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, argumentPattern: ASGNode, resultType: ASGNode) -> None:
        super().__init__(sourceDerivation)
        self.argumentPattern = argumentPattern
        self.resultType = resultType

class ASGSequenceNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, elements: list[ASGNode]) -> None:
        super().__init__(sourceDerivation)
        self.elements = elements

class ASGTupleNode(ASGNode):
    def __init__(self, sourceDerivation: ASGNodeDerivation, elements: list[ASGNode]) -> None:
        super().__init__(sourceDerivation)
        self.elements = elements

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
