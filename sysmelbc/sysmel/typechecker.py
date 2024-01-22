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

    def visitNode(self, node: ASTNode) -> ASTTypedNode | ASTTypeNode:
        return node.accept(self)

    def visitNodeWithExpectedTypeExpression(self, node: ASTNode, expectedTypeExpression: ASTNode) -> ASTTypedNode | ASTTypeNode:
        if expectedTypeExpression is None:
            return self.visitNode(node)

        typedNode = self.visitNode(node)
        typedNodeType = getTypeOfAnalyzedNode(typedNode, typedNode.sourcePosition)
        expectedTypeNode = self.visitTypeExpression(expectedTypeExpression)
        if typedNodeType != expectedTypeNode and not typedNodeType.isEquivalentTo(expectedTypeNode):
            return self.makeSemanticError(node.sourcePosition, "Type checking failure. Value has type '%s' instead of expected type of '%s'." % (typedNode.type.prettyPrint(), expectedTypeNode.prettyPrint()), typedNode, expectedTypeNode)
        return typedNode

    def doesTypedNodeConformToTypeExpression(self, typedNode: ASTTypedNode | ASTTypeNode, expectedTypeExpression: ASTNode | None) -> ASTTypedNode | ASTTypeNode | None:
        typedNodeType = getTypeOfAnalyzedNode(typedNode, typedNode.sourcePosition)
        expectedTypeNode = self.visitTypeExpression(expectedTypeExpression)
        return typedNodeType == expectedTypeNode or typedNodeType.isEquivalentTo(expectedTypeNode)

    def visitNodeWithExpectedType(self, node: ASTNode, expectedType: TypedValue) -> ASTTypedNode | ASTTypeNode:
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
        if analyzedNode.isTypeNode():
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
    
    def betaReducePiWithArgument(self, piNode: ASTNode, argument: ASTNode):
        substitutionContext = SubstitutionContext()
        if piNode.isPiLiteralValue():
            piValue: FunctionalValue = piNode.value
            argumentBinding = piValue.argumentBinding
            piBody = piValue.body
        else:
            assert piNode.isTypedPiNode()
            typedFunctionalNode: ASTTypedFunctionalNode = piNode
            argumentBinding = typedFunctionalNode.argumentBinding
            piBody = typedFunctionalNode.body

        typedArgument = self.visitNodeWithExpectedTypeExpression(argument, argumentBinding.getTypeExpression())
        substitutionContext.setSubstitutionNodeForBinding(argumentBinding, typedArgument)

        reduced = ASTBetaReducer(substitutionContext).visitNode(piBody)
        return typedArgument, reduced
    
    def attemptBetaReducePiWithTypedArgument(self, piNode: ASTNode, typedArgument: ASTNode):
        substitutionContext = SubstitutionContext()
        if piNode.isPiLiteralValue():
            piValue: FunctionalValue = piNode.value
            argumentBinding = piValue.argumentBinding
            piBody = piValue.body
        else:
            assert piNode.isTypedPiNode()
            typedFunctionalNode: ASTTypedFunctionalNode = piNode
            argumentBinding = typedFunctionalNode.argumentBinding
            piBody = typedFunctionalNode.body

        if not self.doesTypedNodeConformToTypeExpression(typedArgument, argumentBinding.getTypeExpression()):
            return None

        substitutionContext.setSubstitutionNodeForBinding(argumentBinding, typedArgument)
        return ASTBetaReducer(substitutionContext).visitNode(piBody)

    def visitArgumentApplicationNode(self, node: ASTArgumentApplicationNode):
        functional = self.visitNode(node.functional)
        if functional.isTypedErrorNode():
            return ASTTypedApplicationNode(node.sourcePosition, functional.type, functional, self.visitNode(node.argument))

        if functional.isTypedPiNodeOrLiteralValue():
            typedArgument, resultType = self.betaReducePiWithArgument(functional, node.argument)
            return resultType
        
        if functional.type.isOverloadsTypeNode():
            acceptedAlternativeTypes = []
            acceptedAlternativeIndices = []
            index = 0
            typedArgument = self.visitNode(node.argument)
            for alternativeType in functional.type.alternativeTypes:
                resultType = self.attemptBetaReducePiWithTypedArgument(alternativeType, typedArgument)
                if resultType is not None:
                    acceptedAlternativeTypes.append(resultType)
                    acceptedAlternativeIndices.append(index)
                index += 1

            print(acceptedAlternativeTypes, acceptedAlternativeIndices)
            assert False

        if not functional.type.isTypedPiNodeOrLiteralValue():
            functional = self.makeSemanticError(functional.sourcePosition, "Application functional must be a forall or it must have a forall type.", functional)
            return ASTTypedApplicationNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbsurdType), functional, self.visitNode(node.argument))
        
        typedArgument, resultType = self.betaReducePiWithArgument(functional.type, node.argument)
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

    def visitPiNode(self, node: ASTPiNode):
        argumentName = self.evaluateOptionalSymbol(node.argumentName)
        argumentType = self.visitOptionalTypeExpression(node.argumentType)
        if argumentName is None and argumentType is None:
            argumentType = ASTLiteralTypeNode(UnitType)

        argumentBinding = SymbolArgumentBinding(node.sourcePosition, argumentName, argumentType)
        lambdaEnvironment = LexicalEnvironment(self.lexicalEnvironment, node.sourcePosition)
        if argumentName is not None:
            lambdaEnvironment = lambdaEnvironment.withSymbolBinding(argumentBinding)
        body = self.withEnvironment(lambdaEnvironment).visitTypeExpression(node.body)
        typedPi = ASTTypedPiNode(node.sourcePosition, mergeTypeUniversesOfTypeNodes(argumentType,  body, node.sourcePosition), argumentBinding, body)
        return typedPi

    def visitFunctionNode(self, node: ASTFunctionNode):
        if len(node.functionalType.arguments) == 0:
            return self.visitNode(ASTLambdaNode(node.sourcePosition, False, None, None, node.functionalType.resultType, node.body))

        resultType = node.functionalType.resultType
        body = node.body
        for argument in reversed(node.functionalType.arguments):
            body = ASTLambdaNode(argument.sourcePosition, argument.isPi, argument.typeExpression, argument.nameExpression, resultType, body)
            resultType = None
        return self.visitNode(body)

    def visitFunctionalTypeNode(self, node: ASTFunctionalTypeNode):
        if len(node.arguments) == 0:
            return self.visitNode(ASTPiNode(node.sourcePosition, None, None, node.resultTypeExpression))

        resultType = node.resultType
        for argument in reversed(node.arguments):
            resultType = ASTPiNode(argument.sourcePosition, argument.typeExpression, argument.nameExpression, resultType)
        return self.visitNode(resultType)
    
    def analyzeIdentifierReferenceNodeWithBinding(self, node: ASTIdentifierReferenceNode, binding: SymbolBinding) -> ASTTypedNode | ASTTypeNode:
        if binding.isValueBinding():
            if binding.value.isType():
                return ASTLiteralTypeNode(node.sourcePosition, binding.value)
            return ASTTypedLiteralNode(node.sourcePosition, binding.getTypeExpression(), binding.value)
        return ASTTypedIdentifierReferenceNode(node.sourcePosition, binding.getTypeExpression(), binding)

    def visitIdentifierReferenceNode(self, node: ASTIdentifierReferenceNode):
        bindingList = self.lexicalEnvironment.lookSymbolBindingListRecursively(node.value)
        if len(bindingList) == 0:
            return self.makeSemanticError(node.sourcePosition, "Failed to find binding for symbol %s." % repr(node.value))
        
        bindingReferenceNodes = list(map(lambda binding: self.analyzeIdentifierReferenceNodeWithBinding(node, binding), bindingList))
        if len(bindingReferenceNodes) == 1:
            return bindingReferenceNodes[0]

        assert len(bindingReferenceNodes) > 1
        tupleNode = ASTOverloadsNode(node.sourcePosition, bindingReferenceNodes)
        return self.visitNode(tupleNode)

    def visitLambdaNode(self, node: ASTLambdaNode):
        argumentName = self.evaluateOptionalSymbol(node.argumentName)
        argumentType = self.visitOptionalTypeExpression(node.argumentType)
        if argumentName is None and argumentType is None:
            argumentType = ASTLiteralTypeNode(UnitType)

        argumentBinding = SymbolArgumentBinding(node.sourcePosition, argumentName, argumentType)
        lambdaEnvironment = LexicalEnvironment(self.lexicalEnvironment, node.sourcePosition)
        if argumentName is not None:
            lambdaEnvironment = lambdaEnvironment.withSymbolBinding(argumentBinding)

        body = self.withEnvironment(lambdaEnvironment).visitNodeWithExpectedTypeExpression(node.body, node.resultType)

        ## Compute the lambda type.
        bodyType = getTypeOfAnalyzedNode(body, node.sourcePosition)
        typedPi = ASTTypedPiNode(node.sourcePosition, mergeTypeUniversesOfTypeNodes(argumentType, bodyType, node.sourcePosition), argumentBinding, bodyType)

        ## Make the lambda node.
        return ASTTypedLambdaNode(node.sourcePosition, typedPi, argumentBinding, body)

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

    def visitOverloadsNode(self, node: ASTOverloadsNode):
        if len(node.alternatives) == 0:
            return self.makeSemanticError(node.sourcePosition, "Overloads node requires at least a single alternative.")
        elif len(node.alternatives) == 1:
            return self.visitNode(node.alternatives[0])

        alternativeTypeExpressions = []
        typedAlternatives = []
        for alternative in node.alternatives:
            typedExpression = self.visitNode(alternative)
            alternativeTypeExpressions.append(getTypeOfAnalyzedNode(typedExpression, typedExpression.sourcePosition))
            typedAlternatives.append(typedExpression)

        overloadsType = reduceOverloadsTypeNode(ASTOverloadsTypeNode(node.sourcePosition, alternativeTypeExpressions))
        return ASTTypedOverloadsNode(node.sourcePosition, overloadsType, typedAlternatives)

    def visitTupleNode(self, node: ASTTupleNode):
        if len(node.elements) == 0:
            return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, UnitType), UnitType.getSingleton())
        elif len(node.elements) == 1:
            return self.visitNode(node.elements[0])
        
        elementTypeExpressions = []
        typedElements = []
        for expression in node.elements:
            typedExpression = self.visitNode(expression)
            elementTypeExpressions.append(getTypeOfAnalyzedNode(typedExpression, typedExpression.sourcePosition))
            typedElements.append(typedExpression)
        
        tupleType = reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, elementTypeExpressions))
        return ASTTypedTupleNode(node.sourcePosition, tupleType, typedElements)

    def visitOverloadsTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitSumTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        return node
    
    def visitTypedErrorNode(self, node: ASTTypedErrorNode):
        return node

    def visitTypedPiNode(self, node: ASTTypedPiNode):
        return node

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode):
        return node

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        return node

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        return node

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode):
        return node

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode):
        return node

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        return node

class SubstitutionContext:
    def __init__(self, parent = None) -> None:
        self.parent = parent
        self.bindingSubstitutionNodes = dict()
        self.bindingSubstitutionBindings = dict()

    def lookSubstitutionForBindingInNode(self, binding: SymbolBinding, oldNode: ASTTypedNode) -> ASTTypedNode | ASTTypeNode:
        if binding in self.bindingSubstitutionNodes:
            return self.applySourcePositionToSubstitution(self.bindingSubstitutionNodes[binding], oldNode.sourcePosition)
        if binding in self.bindingSubstitutionBindings:
            assert oldNode.isTypedIdentifierReferenceNode()
            newBinding = self.bindingSubstitutionBindings[binding]
            return ASTTypedIdentifierReferenceNode(oldNode.sourcePosition, newBinding.getTypeExpression(), newBinding)

        if self.parent is not None:
            return self.parent.lookSubstitutionForBindingInNode(binding, oldNode)
        return oldNode

    def setSubstitutionNodeForBinding(self, binding: SymbolBinding, substitution: ASTTypedNode | ASTTypeNode) -> None:
        self.bindingSubstitutionNodes[binding] = substitution

    def setSubstitutionBindingForBinding(self, binding: SymbolBinding, newBinding: SymbolBinding) -> None:
        self.bindingSubstitutionBindings[binding] = newBinding

    def applySourcePositionToSubstitution(self, substitution: ASTNode, sourcePosition: SourcePosition) -> ASTNode:
        if substitution.isTypedIdentifierReferenceNode():
            return ASTTypedIdentifierReferenceNode(sourcePosition, substitution.type, substitution.binding)
        return substitution

class ASTBetaReducer(ASTTypecheckedVisitor):
    def __init__(self, substitutionContext: SubstitutionContext) -> None:
        super().__init__()
        self.substitutionContext = substitutionContext

    def visitNode(self, node: ASTNode) -> ASTTypedNode | ASTTypeNode:
        return node.accept(self)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode) -> ASTLiteralTypeNode:
        return node
    
    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        return reduceTypedApplicationNode(ASTTypedApplicationNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.functional), self.visitNode(node.argument)))

    def visitTypedErrorNode(self, node: ASTTypedErrorNode):
        return node

    def visitTypedPiNode(self, node: ASTTypedPiNode):
        argumentBinding = node.argumentBinding
        newArgumentBinding = SymbolArgumentBinding(argumentBinding.sourcePosition, argumentBinding.name, self.visitNode(argumentBinding.typeExpression))
        newType = self.visitNode(node.type)
        
        bodyContext = SubstitutionContext(self.substitutionContext)
        bodyContext.setSubstitutionBindingForBinding(argumentBinding, newArgumentBinding)

        reducedBody = ASTBetaReducer(bodyContext).visitNode(node.body)
        return ASTTypedPiNode(node.sourcePosition, newType, newArgumentBinding, reducedBody)

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode):
        return node.binding.evaluateSubstitutionInContextFor(self.substitutionContext, node)

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        argumentBinding = node.argumentBinding
        newArgumentBinding = SymbolArgumentBinding(argumentBinding.sourcePosition, argumentBinding.name, self.visitNode(argumentBinding.typeExpression))
        newType = self.visitNode(node.type)
        
        bodyContext = SubstitutionContext(self.substitutionContext)
        bodyContext.setSubstitutionBindingForBinding(argumentBinding, newArgumentBinding)

        reducedBody = ASTBetaReducer(bodyContext).visitNode(node.body)
        return ASTTypedLambdaNode(node.sourcePosition, newType, newArgumentBinding, reducedBody)

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        return node

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode):
        reducedType = self.visitNode(node.type)
        reducedElements = []
        for element in node.elements:
            reducedElements.append(self.visitNode(element))
        return ASTTypedSequenceNode(node.sourcePosition, reducedType, reducedElements)

    def visitOverloadsTypeNode(self, node: ASTOverloadsTypeNode):
        reducedAlternativeTypes = []
        for alternative in node.alternativeTypes:
            reducedAlternativeTypes.append(self.visitNode(alternative))
        return reduceOverloadsTypeNode(ASTOverloadsTypeNode(node.sourcePosition, reducedAlternativeTypes))

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode):
        reducedType = self.visitNode(node.type)
        reducedAlternatives = []
        for alternative in node.alternatives:
            reducedAlternatives.append(self.visitNode(alternative))
        return reduceTypedOverloadsNode(ASTTypedOverloadsNode(node.sourcePosition, reducedType, reducedAlternatives))

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        reducedElementTypes = []
        for element in node.elementTypes:
            reducedElementTypes.append(self.visitNode(element))
        return reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, reducedElementTypes))

    def visitSumTypeNode(self, node: ASTSumTypeNode):
        reducedAlternativeTypes = []
        for alternative in node.alternativeTypesTypes:
            reducedAlternativeTypes.append(self.visitNode(alternative))
        return reduceSumTypeNode(ASTSumTypeNode(node.sourcePosition, reducedAlternativeTypes))

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        reducedType = self.visitNode(node.type)
        reducedElements = []
        for element in node.elements:
            reducedElements.append(self.visitNode(element))
        return ASTTypedTupleNode(node.sourcePosition, reducedType, reducedElements)
    
def getTypeOfAnalyzedNode(node: ASTTypedNode | ASTTypeNode, sourcePosition: SourcePosition) -> ASTTypedNode | ASTTypeNode:
    if node.isTypeNode():
        return ASTLiteralTypeNode(sourcePosition, node.getTypeUniverse())
    return node.type

def betaReduceFunctionalNodeWithArgument(functionalNode: ASTTypedNode | ASTTypeNode, argument: ASTTypedNode | ASTTypeNode):
    assert functionalNode.isTypedFunctionalNode()
    typedFunctionalNode: ASTTypedFunctionalNode = functionalNode
    argumentBinding = typedFunctionalNode.argumentBinding
    forAllBody = typedFunctionalNode.body

    substitutionContext = SubstitutionContext()
    substitutionContext.setSubstitutionNodeForBinding(argumentBinding, argument)

    return ASTBetaReducer(substitutionContext).visitNode(forAllBody)
    
def makeTypedLiteralForValueAt(value: TypedValue, sourcePosition: SourcePosition) -> ASTTypedLiteralNode | ASTTypeNode:
    if value.isType():
        return ASTLiteralTypeNode(sourcePosition, value)
    return ASTTypedLiteralNode(sourcePosition, ASTLiteralTypeNode(sourcePosition, value.getType()), value)

def reduceTypedApplicationNode(node: ASTTypedApplicationNode):
    hasLiteralArgument = node.argument.isTypeNode() or node.argument.isTypedLiteralNode()
    if not hasLiteralArgument:
        return node

    hasLiteralFunctionalNode = node.isLiteralTypeNode() or node.isTypedLiteralNode()
    if node.functional.isTypedLambdaNode() or node.functional.isTypedPiNode():
        return betaReduceFunctionalNodeWithArgument(node.functional, node.argument)
    
    if hasLiteralFunctionalNode and node.value.isPurelyFunctional():
        return makeTypedLiteralForValueAt(TypedValue = node.functional.value(node.argument.value))

    return node

def isLiteralTypeOfTypeNode(node: ASTNode):
    return (node.isLiteralTypeNode() or node.isTypedLiteralNode()) and node.value.isTypeUniverse()

def reduceType(node: ASTNode):
    if node.isTypedLiteralNode() and isLiteralTypeOfTypeNode(node.type):
        return ASTLiteralTypeNode(node.sourcePosition, node.value)

    return node

def reducePiNode(node: ASTTypedPiNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        forAllValue = PiValue(node.type.value, [], [], node.argumentBinding, node.body)
        return ASTLiteralTypeNode(node.sourcePosition, forAllValue)
    return node

def reduceOverloadsTypeNode(node: ASTOverloadsTypeNode):
    if len(node.alternativeTypes) == 1:
        return node.alternativeTypes[0]
    return node

def reduceTypedOverloadsNode(node: ASTTypedOverloadsNode):
    if len(node.alternatives) == 1:
        return node.alternatives[0]
    return node

def reduceProductTypeNode(node: ASTProductTypeNode):
    if len(node.elementTypes) == 0:
        return ASTLiteralTypeNode(node.sourcePosition, UnitType)
    elif len(node.elementTypes) == 1:
        return node.elementTypes[0]
    return node

def reduceSumTypeNode(node: ASTSumTypeNode):
    if len(node.alternativeTypes) == 0:
        return ASTLiteralTypeNode(node.sourcePosition, AbsurdType)
    elif len(node.alternativeTypes) == 1:
        return node.alternativeTypes[0]
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
