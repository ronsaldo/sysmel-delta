from .scanner import SourcePosition
from .value import *
from abc import ABC, abstractmethod

class ASTVisitor(ABC):
    @abstractmethod
    def visitApplicationNode(self, node):
        pass

    @abstractmethod
    def visitArgumentNode(self, node):
        pass

    @abstractmethod
    def visitBinaryExpressionSequenceNode(self, node):
        pass

    @abstractmethod
    def visitErrorNode(self, node):
        pass

    @abstractmethod
    def visitFunctionalTypeNode(self, node):
        pass

    @abstractmethod
    def visitIdentifierReferenceNode(self, node):
        pass

    @abstractmethod
    def visitLexicalBlockNode(self, node):
        pass

    @abstractmethod
    def visitLambdaNode(self, node):
        pass

    @abstractmethod
    def visitLiteralNode(self, node):
        pass

    @abstractmethod
    def visitMessageSendNode(self, node):
        pass

    @abstractmethod
    def visitSequenceNode(self, node):
        pass

    @abstractmethod
    def visitTupleNode(self, node):
        pass

class ASTNode:
    def __init__(self, sourcePosition: SourcePosition) -> None:
        self.sourcePosition = sourcePosition

class ASTArgumentNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, typeExpression: ASTNode, nameExpression: ASTNode, isForAll: bool = False) -> None:
        super().__init__(sourcePosition)
        self.typeExpression = typeExpression
        self.nameExpression = nameExpression
        self.isForAll = isForAll

    def accept(self, visitor: ASTVisitor):
        return visitor.visitArgumentNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Argument', 'typeExpression': optionalASTNodeToJson(self.typeExpression), 'nameExpression': optionalASTNodeToJson(self.nameExpression), 'isForAll': self.isForAll}

class ASTApplicationNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, functional: ASTNode, arguments: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.functional = functional
        self.arguments = arguments

    def accept(self, visitor: ASTVisitor):
        return visitor.visitApplicationNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Application', 'functional': self.functional.toJson(), 'arguments': list(map(optionalASTNodeToJson, self.arguments))}

class ASTBlockNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, functionalType: ASTNode, body: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.functionalType = functionalType
        self.body = body

    def accept(self, visitor: ASTVisitor):
        return visitor.visitBlockNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Block', 'functionalType': self.functionalType.toJson(), 'body': self.body.toJson()}

class ASTBinaryExpressionSequenceNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitBinaryExpressionSequenceNode(self)

    def toJson(self) -> dict:
        return {'kind': 'BinaryExpressionSequence', 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTErrorNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, message: str) -> None:
        super().__init__(sourcePosition)
        self.message = message

    def accept(self, visitor: ASTVisitor):
        return visitor.visitErrorNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Error', 'message': self.message}

class ASTFunctionalTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, arguments: list[ASTNode], resultTypeExpression: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.arguments = arguments
        self.resultTypeExpression = resultTypeExpression

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFunctionalTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'FunctionalType', 'arguments': list(map(optionalASTNodeToJson, self.arguments)), 'resultTypeExpression': optionalASTNodeToJson(self.resultTypeExpression)}

class ASTIdentifierReferenceNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, value: Symbol) -> None:
        super().__init__(sourcePosition)
        self.value = value

    def accept(self, visitor: ASTVisitor):
        return visitor.visitIdentifierReferenceNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Identifier', 'value': repr(self.value)}

class ASTLambdaNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, functionalType: ASTNode, body: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.functionalType = functionalType
        self.body = body

    def accept(self, visitor: ASTVisitor):
        return visitor.visitLambdaNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Lambda', 'functionalType': self.functionalType.toJson(), 'body': self.body.toJson()}
    
class ASTLexicalBlockNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, expression: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.expression = expression

    def accept(self, visitor: ASTVisitor):
        return visitor.visitLexicalBlockNode(self)

    def toJson(self) -> dict:
        return {'kind': 'LexicalBlock', 'expression': self.expression.toJson()}

class ASTLiteralNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, value: TypedValue) -> None:
        super().__init__(sourcePosition)
        self.value = value

    def accept(self, visitor: ASTVisitor):
        return visitor.visitLiteralNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Literal', 'value': self.value.toJson()}

class ASTMessageSendNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, receiver: ASTNode, selector: ASTNode, arguments: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.receiver = receiver
        self.selector = selector
        self.arguments = arguments

    def accept(self, visitor: ASTVisitor):
        return visitor.visitMessageSendNode(self)

    def toJson(self) -> dict:
        return {'kind': 'MessageSend', 'receiver': optionalASTNodeToJson(self.receiver), 'selector': self.selector.toJson(), 'arguments': list(map(optionalASTNodeToJson, self.arguments))}

class ASTSequenceNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitSequenceNode(self)

    def toJson(self):
        return {'kind': 'Sequence', 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTTupleNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTupleNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Tuple', 'elements': list(map(optionalASTNodeToJson, self.elements))}

def optionalASTNodeToJson(node: ASTNode | None) -> dict | None:
    if node is None:
        return None
    else:
        return node.toJson()

class ASTSequentialVisitor(ASTVisitor):
    def visitNode(self, node: ASTNode):
        return node.accept(self)

    def visitOptionalNode(self, node: ASTNode):
        if node is not None:
            self.visitNode(node)

    def visitApplicationNode(self, node: ASTApplicationNode):
        self.visitNode(node.functional)
        for arg in node.arguments:
            self.visitNode(arg)

    def visitArgumentNode(self, node: ASTArgumentNode):
        self.visitOptionalNode(node.nameExpression)
        self.visitOptionalNode(node.typeExpression)

    def visitBinaryExpressionSequenceNode(self, node: ASTBinaryExpressionSequenceNode):
        for element in node.elements:
            self.visitNode(element)

    def visitErrorNode(self, node: ASTErrorNode):
        pass

    def visitFunctionalTypeNode(self, node: ASTFunctionalTypeNode):
        for arg in node.arguments:
            self.visitNode(arg)
        self.visitOptionalNode(node.resultTypeExpression)

    def visitIdentifierReferenceNode(self, node: ASTIdentifierReferenceNode):
        pass

    def visitLexicalBlockNode(self, node: ASTLexicalBlockNode):
        self.visitNode(node.expression)

    def visitLambdaNode(self, node: ASTLambdaNode):
        self.visitNode(node.functionalType)
        self.visitNode(node.body)

    def visitLiteralNode(self, node):
        pass

    def visitMessageSendNode(self, node: ASTMessageSendNode):
        self.visitOptionalNode(node.receiver)
        self.visitNode(node.selector)
        for arg in node.arguments:
            self.visitNode(arg)

    def visitSequenceNode(self, node: ASTSequenceNode):
        for expression in node.elements:
            self.visitNode(expression)

    def visitTupleNode(self, node: ASTTupleNode):
        for expression in node.elements:
            self.visitNode(expression)

class ASTErrorVisitor(ASTSequentialVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.errorNodes = []
    
    def visitErrorNode(self, node: ASTErrorNode):
        self.errorNodes.append(node)

    def checkASTAndPrintErrors(self, node: ASTNode):
        self.visitNode(node)
        for errorNode in self.errorNodes:
            print('%s: %s' % (str(errorNode.sourcePosition), errorNode.message))
        return len(self.errorNodes) == 0
