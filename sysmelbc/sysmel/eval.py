from .ast import *
from .value import *

class ASTEvaluator(ASTVisitor):
    def visitNode(self, node: ASTNode) ->TypedValue:
        return node.accept(self)

    def evaluate(self, ast: ASTNode) -> TypedValue:
        return self.visitNode(ast)

    def visitApplicationNode(self, node):
        assert False

    def visitArgumentNode(self, node):
        assert False

    def visitBinaryExpressionSequenceNode(self, node):
        assert False

    def visitErrorNode(self, node: ASTErrorNode):
        raise Exception("%s: %s" % (str(node.sourcePosition), node.message))

    def visitFunctionalTypeNode(self, node):
        assert False

    def visitIdentifierReferenceNode(self, node):
        assert False

    def visitLexicalBlockNode(self, node):
        assert False

    def visitLambdaNode(self, node):
        assert False

    def visitLiteralNode(self, node: ASTLiteralNode):
        return node.value

    def visitMessageSendNode(self, node):
        assert False

    def visitSequenceNode(self, node: ASTSequenceNode):
        result = UnitType.getSingleton()
        for expression in node.elements:
            result = self.visitNode(expression)
        return result

    def visitTupleNode(self, node: ASTTupleNode):
        if len(node.elements) == 0:
            return UnitType.getSingleton()
        elif len(node.elements) == 1:
            return self.visitNode(node.elements[0])

        elements = []
        elementTypes = []
        for expression in node.elements:
            value = self.visitNode(expression)
            elements.append(value)
            elementTypes.append(value.getType())

        resultType = ProductType(elementTypes)
        return resultType.makeWithElements(tuple(elements))
    