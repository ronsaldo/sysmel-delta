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

    def visitForAllNode(self, node: ASTFunctionNode):
        assert False

    def visitFunctionNode(self, node: ASTFunctionNode):
        if len(node.functionalType.arguments) == 0:
            return self.visitNode(ASTLambdaNode(node.sourcePosition, None, None, node.functionalType.resultType, node.body))

        resultType = node.functionalType.resultType
        body = node.body
        for argument in reversed(node.functionalType.arguments):
            if argument.isForAll:
                if resultType is not None:
                    body = ASTLambdaNode(argument.sourcePosition, None, None, resultType, body)
                    resultType = None
                body = ASTForAllNode(argument.sourcePosition, argument.typeExpression, argument.nameExpression, body)
            else:
                body = ASTLambdaNode(argument.sourcePosition, argument.typeExpression, argument.nameExpression, resultType, body)
            resultType = None
        return self.visitNode(body)

    def visitFunctionalTypeNode(self, node: ASTFunctionalTypeNode):
        if len(node.arguments) == 0:
            return self.visitNode(ASTForAllNode(node.sourcePosition, None, None, node.resultTypeExpression))

        resultType = node.resultType
        for argument in reversed(node.arguments):
            resultType = ASTForAllNode(argument.sourcePosition, argument.typeExpression, argument.nameExpression, resultType)
        return self.visitNode(resultType)

    def visitIdentifierReferenceNode(self, node: ASTIdentifierReferenceNode):
        assert False

    def visitLambdaNode(self, node: ASTFunctionNode):
        assert False

    def visitLexicalBlockNode(self, node: ASTLexicalBlockNode):
        assert False

    def visitLiteralNode(self, node: ASTLiteralNode):
        return ASTTypedLiteralNode(node.sourcePosition, node.value.getType(), node.value)

    def visitMessageSendNode(self, node: ASTMessageSendNode):
        assert False

    def visitSequenceNode(self, node: ASTSequenceNode):
        if len(node.elements) == 0:
            return ASTTypedLiteralNode(node.sourcePosition, UnitType, UnitType.getSingleton())
        elif len(node.elements) == 1:
            return self.visitNode(node.elements[0])
        
        resultType = UnitType
        typedElements = []
        for expression in node.elements:
            typedExpression = self.visitNode(expression)
            resultType = typedExpression.type
            typedElements.append(typedExpression)
        return ASTTypedSequenceNode(node.sourcePosition, resultType, typedElements)

    def visitTupleNode(self, node: ASTTupleNode):
        if len(node.elements) == 0:
            return ASTTypedLiteralNode(node.sourcePosition, UnitType, UnitType.getSingleton())
        elif len(node.elements) == 1:
            return self.visitNode(node.elements[0])
        
        elementTypes = []
        typedElements = []
        for expression in node.elements:
            typedExpression = self.visitNode(expression)
            elementTypes.append(typedExpression.type)
            typedElements.append(typedExpression)
        return ASTTupleNode(node.sourcePosition, ProductType.makeWithElementTypes(elementTypes), typedElements)

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
