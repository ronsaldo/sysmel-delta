from .ast import *

class ErrorAccumulator:
    def __init__(self) -> None:
        self.errorList = []

    def add(self, errorNode):
        self.errorList.append(errorNode)

    def printErrors(self):
        if len(self.errorList) == 0: return True
        
        for error in self.errorList:
            print('%s: %s' % (error.sourcePosition, error.message))
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
        expectedTypeNode = self.visitTypeExpression(expectedTypeExpression)
        if typedNode.type != expectedTypeNode and not typedNode.type.isEquivalentTo(expectedTypeNode):
            return self.makeSemanticError(node.sourcePosition, "Type checking failure. Value has type '%s' instead of expected type of '%s'." % (typedNode.type.prettyPrint(), expectedTypeNode.prettyPrint()), typedNode, expectedTypeNode)
        return typedNode

    def visitNodeWithExpectedType(self, node: ASTNode, expectedType: TypedValue) -> ASTTypedNode | ASTLiteralTypeNode:
        if expectedType is None:
            return self.visitNode(node)

        return self.visitNodeWithExpectedTypeExpression(node, ASTLiteralTypeNode(node.sourcePosition, expectedType))

    def evaluateSymbol(self, node: ASTNode) -> Symbol | None:
        return self.evaluateReducedLiteral(self.visitNodeWithExpectedType(node, SymbolType))

    def evaluateOptionalSymbol(self, node: ASTNode) -> Symbol | None:
        if node is None:
            return None
        
        symbol, errorNode = self.evaluateSymbol(node)
        return symbol
    
    def evaluateReducedLiteral(self, node: ASTTypedNode) -> TypedValue | None:
        if node.isTypedLiteralNode():
            return node.value, None

        return None, self.makeSemanticError(node.sourcePosition, "Expected a value reducible expression.", node)
    
    def visitTypeExpression(self, node: ASTNode) -> ASTTypedNode:
        analyzedNode = self.visitNode(node)
        if analyzedNode.isLiteralTypeNode():
            return analyzedNode
        
        if isLiteralTypeOfTypeNode(analyzedNode.type):
            return reduceType(analyzedNode)

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
    
    def makeSemanticError(self, sourcePosition: SourcePosition, errorMessage: str, innerNode: ASTNode = None, innerNode2: ASTNode = None) -> ASTTypedErrorNode:
        innerNodes = []
        if innerNode is not None:
            innerNodes.append(innerNode)
        if innerNode2 is not None:
            innerNodes.append(innerNode2)
        errorNode = ASTTypedErrorNode(sourcePosition, ASTLiteralTypeNode(sourcePosition, AbsurdType), errorMessage, innerNodes)
        self.errorAccumulator.add(errorNode)
        return errorNode

    def visitApplicationNode(self, node: ASTApplicationNode):
        functional = self.visitNode(node.functional)
        if len(node.arguments) == 0:
            return self.visitNode(ASTArgumentApplicationNode(node.sourcePosition, functional, ASTLiteralNode(node.sourcePosition, UnitType.getSingleton())))

        for argument in node.arguments:
            functional = self.visitNode(ASTArgumentApplicationNode(argument.sourcePosition, functional, argument))
        return functional
    
    def betaReduceForAllWithArgument(self, forAllNode: ASTNode, argument: ASTNode):
        if forAllNode.isTypedForAllNode():
            typedForAllNode: ASTTypedForAllNode = forAllNode
            argumentBinding = typedForAllNode.argumentBinding
            captureBindings = typedForAllNode.captureBindings
            forAllBody = typedForAllNode.body
        else:
            assert forAllNode.isForAllLiteralValue()
            forAllValue: ForAllValue = forAllNode.value
            argumentBinding = forAllValue.argumentBinding
            captureBindings = []
            forAllBody = forAllValue.body

        typedArgument = self.visitNodeWithExpectedTypeExpression(argument, argumentBinding.getTypeExpression())

        substitutionContext = SubstitutionContext(captureBindings, list(map(captureBindingToIdentifierReferenceNode, captureBindings)), argumentBinding, typedArgument)
        reduced = ASTBetaSubstituter(substitutionContext).visitNode(forAllBody)
        return typedArgument, reduced

    def visitArgumentApplicationNode(self, node: ASTArgumentApplicationNode):
        functional = self.visitNode(node.functional)
        if functional.isTypedErrorNode():
            return ASTTypedApplicationNode(node.sourcePosition, functional.type, functional, self.visitNode(node.argument))

        if functional.isTypedForAllNodeOrLiteralValue():
            typedArgument, resultType = self.betaReduceForAllWithArgument(functional, node.argument)
            return resultType

        if not functional.type.isTypedForAllNodeOrLiteralValue():
            functional = self.makeSemanticError(functional.sourcePosition, "Application functional must be a forall or it must have a forall type.", functional)
            return ASTTypedApplicationNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbsurdType), functional, self.visitNode(node.argument))
        
        typedArgument, resultType = self.betaReduceForAllWithArgument(functional.type, node.argument)
        return reduceTypedApplicationNode(ASTTypedApplicationNode(node.sourcePosition, resultType, functional, typedArgument))

    def visitArgumentNode(self, node: ASTArgumentNode):
        assert False

    def visitBinaryExpressionSequenceNode(self, node: ASTBinaryExpressionSequenceNode):
        if len(node.elements) == 3:
            return self.visitNode(ASTMessageSendNode(node.sourcePosition, node.elements[0], node.elements[1], [node.elements[2]]))
        assert False

    def visitErrorNode(self, node: ASTErrorNode):
        errorNode = ASTTypedErrorNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbsurdType), node.message)
        self.errorAccumulator.add(errorNode)
        return errorNode

    def visitForAllNode(self, node: ASTForAllNode):
        lambdaEnvironment = LambdaEnvironment(self.lexicalEnvironment, node.sourcePosition)
        argumentName = self.evaluateOptionalSymbol(node.argumentName)
        argumentType = self.visitOptionalTypeExpression(node.argumentType)
        if argumentName is None and argumentType is None:
            argumentType = ASTLiteralTypeNode(UnitType)

        argumentBinding = SymbolArgumentBinding(node.sourcePosition, argumentName, argumentType)
        lambdaEnvironment.setArgumentBinding(argumentBinding)
        body = self.withEnvironment(lambdaEnvironment).visitTypeExpression(node.body)
        typedForAll = ASTTypedForAllNode(node.sourcePosition, mergeTypeUniversesOfTypeNodes(argumentType,  body, node.sourcePosition), lambdaEnvironment.captureBindings, argumentBinding, body)
        return reduceForAllNode(typedForAll)

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
        bodyType = getTypeOfTypedNodeOrLiteralType(body, node.sourcePosition)
        typedForAll = ASTTypedForAllNode(node.sourcePosition, mergeTypeUniversesOfTypeNodes(argumentType, bodyType, node.sourcePosition), lambdaEnvironment.captureBindings, argumentBinding, bodyType)
        reducedForAll = reduceForAllNode(typedForAll)

        ## Make the lambda node.
        lambdaNode = ASTTypedLambdaNode(node.sourcePosition, reducedForAll, lambdaEnvironment.captureBindings, argumentBinding, body)
        return reduceLambdaNode(lambdaNode)

    def visitLexicalBlockNode(self, node: ASTLexicalBlockNode):
        innerEnvironment = LexicalEnvironment(self.lexicalEnvironment)
        return Typechecker(innerEnvironment, self.errorAccumulator).visitNode(node)

    def visitLiteralNode(self, node: ASTLiteralNode):
        return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, node.value.getType()), node.value)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode):
        return node

    def visitMessageSendNode(self, node: ASTMessageSendNode):
        selector, errorNode = self.evaluateSymbol(node.selector)
        if selector is not None:
            selectorNode = ASTIdentifierReferenceNode(node.selector.sourcePosition, selector)
        else:
            selectorNode = errorNode
        
        if node.receiver is None:
            return self.visitNode(ASTApplicationNode(node.sourcePosition, selectorNode, node.arguments))
        else:
            return self.visitNode(ASTApplicationNode(node.sourcePosition, selectorNode, [node.receiver] + node.arguments))

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
        return ASTTypedTupleNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, ProductType.makeWithElementTypes(elementTypes)), typedElements)

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        return node
    
    def visitTypedErrorNode(self, node: ASTTypedErrorNode):
        return node

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

class ASTBetaSubstituter(ASTTypecheckedVisitor):
    def __init__(self, substitutionContext: SubstitutionContext) -> None:
        super().__init__()
        self.substitutionContext = substitutionContext

    def visitNode(self, node: ASTNode) -> ASTTypedNode | ASTLiteralTypeNode:
        return node.accept(self)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode) -> ASTLiteralTypeNode:
        return node
    
    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        return reduceTypedApplicationNode(ASTTypedApplicationNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.functional), self.visitNode(node.argument)))

    def visitTypedErrorNode(self, node: ASTTypedErrorNode):
        return node

    def visitTypedForAllNode(self, node: ASTTypedForAllNode):
        assert False

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode):
        return node.binding.evaluateSubstitutionInContext(self.substitutionContext, node.sourcePosition)

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        assert False

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        return node

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode):
        assert False

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        assert False
    
def getTypeOfTypedNodeOrLiteralType(node: ASTTypedNode | ASTLiteralTypeNode, sourcePosition: SourcePosition) -> ASTTypedNode | ASTLiteralTypeNode:
    if node.isLiteralTypeNode():
        return ASTLiteralTypeNode(sourcePosition, node.value.getType())
    return node.type

def reduceTypedApplicationNode(node: ASTTypedApplicationNode):
    return node

def isLiteralTypeOfTypeNode(node: ASTNode):
    return (node.isLiteralTypeNode() or node.isTypedLiteralNode()) and node.value.isTypeUniverse()

def reduceType(node: ASTNode):
    if node.isTypedLiteralNode() and isLiteralTypeOfTypeNode(node.type):
        return ASTLiteralTypeNode(node.sourcePosition, node.value)

    return node

def reduceForAllNode(node: ASTTypedForAllNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        forAllValue = ForAllValue(node.type.value, [], [], node.argumentBinding, node.body)
        return ASTLiteralTypeNode(node.sourcePosition, forAllValue)
    return node

def reduceLambdaNode(node: ASTTypedLambdaNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        lambdaValue = LambdaValue(node.type.value, [], [], node.argumentBinding, node.body)
        return ASTTypedLiteralNode(node.sourcePosition, node.type, lambdaValue)
    return node

def mergeTypeUniversesOfTypeNodes(leftNode: ASTTypedNode, rightNode: ASTTypedNode, sourcePosition: SourcePosition) -> ASTLiteralTypeNode:
    leftUniverseIndex = leftNode.computeTypeUniverseIndex()
    rightUniverseIndex = rightNode.computeTypeUniverseIndex()
    mergedUniverse = max(leftUniverseIndex, rightUniverseIndex)
    return ASTLiteralTypeNode(sourcePosition, TypeUniverse.getWithIndex(mergedUniverse))

def captureBindingToIdentifierReferenceNode(captureBinding: SymbolCaptureBinding) -> ASTTypedIdentifierReferenceNode:
    return ASTTypedIdentifierReferenceNode(captureBinding.sourcePosition, captureBinding.getTypeExpression(), captureBinding.capturedBinding)

