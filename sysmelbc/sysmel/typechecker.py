from .ast import *

class ErrorAccumulator:
    def __init__(self) -> None:
        self.errorList = []

    def add(self, errorNode):
        self.errorList.append(errorNode)

    def printErrors(self):
        if len(self.errorList) == 0: return True
        
        for error in self.errorList:
            print('%s: %s', error.sourcePosition, error.message)
        return False

class Typechecker(ASTVisitor):
    def __init__(self, lexicalEnvironment: LexicalEnvironment, errorAccumulator: ErrorAccumulator = None):
        self.lexicalEnvironment = lexicalEnvironment
        self.errorAccumulator = errorAccumulator
        if self.errorAccumulator is None:
            self.errorAccumulator = ErrorAccumulator()

    def withEnvironment(self, newEnvironment: LexicalEnvironment):
        return Typechecker(newEnvironment, self.errorAccumulator)

    def visitNode(self, node: ASTNode) -> ASTTypedNode | ASTLiteralTypeNode:
        return node.accept(self)

    def visitNodeWithExpectedTypeExpression(self, node: ASTNode, expectedTypeExpression: ASTNode | None) -> ASTTypedNode | ASTLiteralTypeNode:
        if expectedTypeExpression is None:
            return self.visitNode(node)

        typedNode = self.visitNode(node)
        ## TODO: Typecheck the node
        return typedNode

    def visitNodeWithExpectedType(self, node: ASTNode, expectedType: TypedValue) -> ASTTypedNode | ASTLiteralTypeNode:
        if expectedType is None:
            return self.visitNode(node)

        return self.visitNodeWithExpectedTypeExpression(node, ASTLiteralTypeNode(node.sourcePosition, expectedType))

    def evaluateOptionalSymbol(self, node: ASTNode) -> Symbol | None:
        if node is None:
            return None
        
        return self.evaluateReducedLiteral(self.visitNodeWithExpectedType(node, SymbolType))
    
    def evaluateReducedLiteral(self, node: ASTTypedNode) -> TypedValue | None:
        if node.isTypedLiteralNode():
            return node.value

        self.makeSemanticError(node.sourcePosition, "Expected a value reducible expression.", node)
        return None
    
    def mergeTypeUniversesOfTypeNodes(self, leftNode: ASTTypedNode, rightNode: ASTTypedNode, sourcePosition: SourcePosition) -> ASTLiteralTypeNode:
        leftUniverseIndex = leftNode.computeTypeUniverseIndex()
        rightUniverseIndex = rightNode.computeTypeUniverseIndex()
        mergedUniverse = max(leftUniverseIndex, rightUniverseIndex)
        assert mergedUniverse >= 1
        return ASTLiteralTypeNode(sourcePosition, TypeUniverse.getWithIndex(mergedUniverse - 1))

    def visitTypeExpression(self, node: ASTNode) -> ASTTypedNode:
        analyzedNode = self.visitNode(node)
        if analyzedNode.isLiteralTypeNode():
            return analyzedNode
        
        if analyzedNode.type.isLiteralTypeNode():
            if analyzedNode.type.value.isTypeUniverse():
                return analyzedNode

        if analyzedNode.isTypedErrorNode():
            return ASTLiteralTypeNode(node.sourcePosition, AbsurdType)

        return self.makeSemanticError(node.sourcePosition, "Expression is not a type.", analyzedNode)

    def visitOptionalTypeExpression(self, node: ASTNode) -> ASTTypedNode:
        if node is None:
            return None
        return self.visitTypeExpression(node)

    def typecheckASTAndPrintErrors(self, node: ASTNode) -> tuple[ASTTypedNode, bool]:
        result = self.visitNode(node)
        return result, self.errorAccumulator.printErrors()
    
    def makeSemanticError(self, sourcePosition: SourcePosition, errorMessage: str, innerNode: ASTNode = None) -> ASTTypedErrorNode:
        errorNode = ASTTypedErrorNode(sourcePosition, AbsurdType, errorMessage, innerNode)
        self.errorAccumulator.add(errorNode)
        return errorNode

    def visitApplicationNode(self, node: ASTApplicationNode):
        functional = self.visitNode(node.functional)

        assert False

    def visitArgumentNode(self, node: ASTArgumentNode):
        assert False

    def visitBinaryExpressionSequenceNode(self, node: ASTBinaryExpressionSequenceNode):
        assert False

    def visitErrorNode(self, node: ASTErrorNode):
        assert False

    def reduceForAllNode(self, node: ASTTypedForAllNode):
        if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
            forAllValue = ForAllValue(node.type.value, [], [], node.argumentBinding, node.body)
            return ASTLiteralTypeNode(node.sourcePosition, forAllValue)
        return node

    def reduceLambda(self, node: ASTTypedLambdaNode):
        if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
            lambdaValue = LambdaValue(node.type.value, [], [], node.argumentBinding, node.body)
            return ASTTypedLiteralNode(node.sourcePosition, node.type, lambdaValue)
        return node

    def visitForAllNode(self, node: ASTForAllNode):
        lambdaEnvironment = LambdaEnvironment(self.lexicalEnvironment, node.sourcePosition)
        argumentName = self.evaluateOptionalSymbol(node.argumentName)
        argumentType = self.visitOptionalTypeExpression(node.argumentType)
        if argumentName is None and argumentType is None:
            argumentType = ASTLiteralTypeNode(UnitType)

        argumentBinding = SymbolArgumentBinding(node.sourcePosition, argumentName, argumentType)
        lambdaEnvironment.setArgumentBinding(argumentBinding)
        body = self.withEnvironment(lambdaEnvironment).visitTypeExpression(node.body)
        forAllUniverse = self.mergeTypeUniversesOfTypeNodes(argumentType, body, node.sourcePosition)
        typedForAll = ASTTypedForAllNode(node.sourcePosition, forAllUniverse, lambdaEnvironment.captureBindings, argumentBinding, body)
        return self.reduceForAllNode(typedForAll)

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
        binding = self.lexicalEnvironment.lookSymbolRecursively(node.value)
        if binding is None:
            return self.makeSemanticError(node.sourcePosition, "Failed to find binding for symbol %s." % repr(node.value))
        
        if binding.isValueBinding():
            return ASTTypedLiteralNode(node.sourcePosition, binding.getTypeExpression(), binding.value)
        return ASTTypedIdentifierReferenceNode(node.sourcePosition, binding.getTypeExpression(), binding)

    def visitLambdaNode(self, node: ASTLambdaNode):
        lambdaEnvironment = LambdaEnvironment(self.lexicalEnvironment, node.sourcePosition)
        argumentName = self.evaluateOptionalSymbol(node.argumentName)
        argumentType = self.visitOptionalTypeExpression(node.argumentType)
        if argumentName is None and argumentType is None:
            argumentType = ASTLiteralTypeNode(UnitType)

        argumentBinding = SymbolArgumentBinding(node.sourcePosition, argumentName, argumentType)
        lambdaEnvironment.setArgumentBinding(argumentBinding)

        body = self.withEnvironment(lambdaEnvironment).visitNodeWithExpectedTypeExpression(node.body, node.resultType)

        ## Compute the lambda type.
        bodyType = body.type
        forAllUniverse = self.mergeTypeUniversesOfTypeNodes(argumentType, bodyType, node.sourcePosition)
        typedForAll = ASTTypedForAllNode(node.sourcePosition, forAllUniverse, lambdaEnvironment.captureBindings, argumentBinding, bodyType)
        reducedForAll = self.reduceForAllNode(typedForAll)

        ## Make the lambda node.
        lambdaNode = ASTTypedLambdaNode(node.sourcePosition, reducedForAll, lambdaEnvironment.captureBindings, argumentBinding, body)
        return self.reduceLambda(lambdaNode)

    def visitLexicalBlockNode(self, node: ASTLexicalBlockNode):
        assert False

    def visitLiteralNode(self, node: ASTLiteralNode):
        return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, node.value.getType()), node.value)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode):
        return node

    def visitMessageSendNode(self, node: ASTMessageSendNode):
        assert False

    def visitSequenceNode(self, node: ASTSequenceNode):
        if len(node.elements) == 0:
            return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, UnitType), UnitType.getSingleton())
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
            return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, UnitType), UnitType.getSingleton())
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
