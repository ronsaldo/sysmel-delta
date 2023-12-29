from .ast import *

class Typechecker(ASTVisitor):
    def visitNode(self, node: ASTNode) -> ASTTypedNode:
        return node.accept(self)

    def typecheckASTAndPrintErrors(self, node: ASTNode) -> ASTTypedNode:
        result = self.visitNode(node)
        return result

    def visitApplicationNode(self, node: ASTApplicationNode):
        assert False

    def visitArgumentNode(self, node: ASTArgumentNode):
        assert False

    def visitBinaryExpressionSequenceNode(self, node: ASTBinaryExpressionSequenceNode):
        assert False

    def visitErrorNode(self, node: ASTErrorNode):
        assert False

    def visitFunctionNode(self, node: ASTFunctionNode):
        assert False

    def visitFunctionalTypeNode(self, node: ASTFunctionalTypeNode):
        assert False

    def visitIdentifierReferenceNode(self, node: ASTIdentifierReferenceNode):
        assert False

    def visitLexicalBlockNode(self, node: ASTLexicalBlockNode):
        assert False

    def visitLiteralNode(self, node: ASTLiteralNode):
        assert False

    def visitMessageSendNode(self, node: ASTMessageSendNode):
        assert False

    def visitSequenceNode(self, node: ASTSequenceNode):
        if len(node.elements) == 0:
            return ASTTypedLiteralNode(node.sourcePosition, UnitType, UnitType.getSingleton())
        elif len(node.elements) == 1:
            return self.visitNode(node.elements[0])
        
        resultType = UnitType
        #typedElements = 
        assert False

    def visitTupleNode(self, node: ASTTupleNode):
        assert False

    def visitTypedForAllNode(self, node: ASTTypedForAllNode):
        return node

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode):
        return node

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        return node

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        return node

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode):
        return node

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        return node
