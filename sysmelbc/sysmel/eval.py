from .ast import *
from .value import *

class ASTEvaluator(ASTTypecheckedVisitor):
    def visitNode(self, node: ASTNode) ->TypedValue:
        return node.accept(self)

    def evaluate(self, ast: ASTNode) -> TypedValue:
        return self.visitNode(ast)

    def visitTypedForAllNode(self, node) -> TypedValue:
        assert False

    def visitTypedIdentifierReferenceNode(self, node) -> TypedValue:
        assert False

    def visitTypedLambdaNode(self, node) -> TypedValue:
        assert False

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode) -> TypedValue:
        return node.value

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode) -> TypedValue:
        result = UnitType.getSingleton()
        for expression in node.elements:
            result = self.visitNode(expression)
        return result

    def visitTypedTupleNode(self, node) -> TypedValue:
        assert False
