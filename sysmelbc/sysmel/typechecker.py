from .ast import *
from .environment import *

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

    def attemptToVisitNodeWithExpectedTypeExpression(self, node: ASTNode, expectedTypeExpression: ASTNode) -> tuple[ASTTypedNode | ASTTypeNode, str | None]:
        typedNode = self.visitNode(node)

        if expectedTypeExpression is None:
            return [], typedNode, None

        expectedTypeNode = self.visitTypeExpression(expectedTypeExpression)
        startingEnvironment = self.lexicalEnvironment
        doesTypeCheck, newEnvironment = self.doesTypedNodeConformToTypeExpression(typedNode, expectedTypeNode)
        implicitValueSubstitutions = newEnvironment.getImplicitValueSubstitutionsUpTo(startingEnvironment)
        if not doesTypeCheck:
            return implicitValueSubstitutions, typedNode, "Type checking failure. Value has type '%s' instead of expected type of '%s'." % (getTypeOfAnalyzedNode(typedNode, typedNode.sourcePosition).prettyPrint(), expectedTypeNode.prettyPrint())
        
        return implicitValueSubstitutions, typedNode, None
    
    def attemptToVisitNodeWithExpectedType(self, node: ASTNode, expectedType: TypedValue) -> tuple[ASTTypedNode | ASTTypeNode, str | None]:
        return self.attemptToVisitNodeWithExpectedTypeExpression(node, ASTLiteralTypeNode(node.sourcePosition, expectedType))

    def doesTypedNodeConformToTypeExpression(self, typedNode: ASTTypedNode | ASTTypeNode, expectedTypeExpression: ASTNode | None) -> ASTTypedNode | ASTTypeNode | None:
        typedNodeType = getTypeOfAnalyzedNode(typedNode, typedNode.sourcePosition)
        expectedTypeNode = self.visitTypeExpression(expectedTypeExpression)
        return expectedTypeNode.performEquivalenceCheckInEnvironment(typedNodeType, self.lexicalEnvironment)
    
    def visitNodeWithExpectedType(self, node: ASTNode, expectedType: TypedValue) -> ASTTypedNode | ASTTypeNode:
        if expectedType is None:
            return self.visitNode(node)

        return self.visitNodeWithExpectedTypeExpression(node, ASTLiteralTypeNode(node.sourcePosition, expectedType))

    def evaluateSymbol(self, node: ASTNode) -> Symbol | None:
        return self.evaluateReducedLiteral(self.visitNodeWithExpectedType(node, SymbolType))

    def evaluateString(self, node: ASTNode) -> Symbol | None:
        return self.evaluateReducedLiteral(self.visitNodeWithExpectedType(node, StringType))

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
        isImplicit = node.kind == ASTApplicationNode.Bracket

        if len(node.arguments) == 0:
            return self.visitNode(ASTArgumentApplicationNode(node.sourcePosition, functional, ASTLiteralNode(node.sourcePosition, UnitType.getSingleton()), isImplicit = isImplicit))

        for argument in node.arguments:
            functional = self.visitNode(ASTArgumentApplicationNode(argument.sourcePosition, functional, argument, isImplicit = isImplicit))
        return functional
    
    def attemptBetaReducePiWithTypedArgument(self, piNode: ASTNode, argument: ASTNode, isImplicitApplication = False):
        substitutionContext = SubstitutionContext()
        if piNode.isFunctionTypeLiteralValue():
            functionType: FunctionType = piNode.value
            if isImplicitApplication:
                return None, self.visitNode(argument), None, [], "Unexpected implicit argument application, when an explicit argument of type %s is required." % functionType.resultType.prettyPrint()
            
            implicitValueSubstitutions, typedArgument, errorMessage = self.attemptToVisitNodeWithExpectedType(argument, functionType.argumentType)
            if errorMessage is not None:
                return None, typedArgument, None, implicitValueSubstitutions, errorMessage

            resultTypeNode = ASTLiteralTypeNode(argument.sourcePosition, functionType.resultType)
            return None, typedArgument, resultTypeNode, implicitValueSubstitutions, None
        
        elif piNode.isTypedFunctionTypeNode():
            assert False
        elif piNode.isPiLiteralValue():
            piValue: FunctionalValue = piNode.value
            argumentBinding = piValue.argumentBinding
            piBody = piValue.body
        else:
            assert piNode.isTypedPiNode()
            typedFunctionalNode: ASTTypedFunctionalNode = piNode
            argumentBinding = typedFunctionalNode.argumentBinding
            piBody = typedFunctionalNode.body

        if isImplicitApplication and not argumentBinding.isImplicit:
            return None, self.visitNode(argument), None, [], "Unexpected implicit argument application, when an explicit argument of type %s is required." % argumentBinding.getTypeExpression().prettyPrint()

        ## Are we missing implicit arguments that need to be inferred?
        if argumentBinding.isImplicit and not isImplicitApplication:
            placeHolderBinding = SymbolImplicitValueBinding(argument.sourcePosition, argumentBinding.name, argumentBinding.getTypeExpression())
            implicitArgumentValueNode = ASTTypedIdentifierReferenceNode(argument.sourcePosition, placeHolderBinding.typeExpression, placeHolderBinding)

            substitutionContext.setSubstitutionNodeForBinding(argumentBinding, implicitArgumentValueNode)
            reduced = ASTBetaReducer(substitutionContext).visitNode(piBody)
            return implicitArgumentValueNode, argument, reduced, [], None

        implicitValueSubstitutions, typedArgument, errorMessage = self.attemptToVisitNodeWithExpectedTypeExpression(argument, argumentBinding.getTypeExpression())
        if errorMessage is not None:
            return None, typedArgument, None, implicitValueSubstitutions, errorMessage

        substitutionContext.setSubstitutionNodeForBinding(argumentBinding, typedArgument)

        reduced = ASTBetaReducer(substitutionContext).visitNode(piBody)
        return None, typedArgument, reduced, implicitValueSubstitutions, errorMessage

    def visitArgumentApplicationNode(self, node: ASTArgumentApplicationNode):
        functional = self.visitNode(node.functional)
        if functional.isTypedErrorNode():
            return ASTTypedApplicationNode(node.sourcePosition, functional.type, functional, self.visitNode(node.argument), [])
        
        if isMacroValueNode(functional):
            macroValue = functional.value
            if macroValue.expectsMacroEvaluationContext():
                macroValue = macroValue(MacroContext(node.sourcePosition, self.lexicalEnvironment, self))
            macroEvaluationResult = macroValue(node.argument)

            if macroEvaluationResult.isMacroValue():
                return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, macroEvaluationResult.getType()), macroEvaluationResult)
            assert isinstance(macroEvaluationResult, ASTNode)
            return self.visitNode(macroEvaluationResult)

        if functional.isAnyFunctionTypeNode():
            pendingInferenceArgument, typedArgument, resultType, implicitValueSubstitutions, errorMessage = self.attemptBetaReducePiWithTypedArgument(functional, node.argument, isImplicitApplication = node.isImplicit)
            if errorMessage is not None:
                return self.makeSemanticError(node.sourcePosition, errorMessage, functional, typedArgument)

            assert pendingInferenceArgument is None
            return resultType
        
        functionalType = getTypeOfAnalyzedNode(functional, node.sourcePosition)
        if functionalType.isOverloadsTypeNode():
            acceptedAlternativeTypes = []
            acceptedAlternativeIndices = []
            acceptedAlternativeImplicitValueSubstitutions = []
            index = 0
            typedArgument = self.visitNode(node.argument)
            for alternativeType in functional.type.alternativeTypes:
                pendingInferenceArgument, alternativeTypedArgument, resultType, implicitValueSubstitutions, errorMessage = self.attemptBetaReducePiWithTypedArgument(alternativeType, typedArgument, isImplicitApplication = node.isImplicit)
                assert pendingInferenceArgument is None
                if errorMessage is None:
                    acceptedAlternativeImplicitValueSubstitutions.append(implicitValueSubstitutions)

                    acceptedAlternativeTypes.append(resultType)
                    acceptedAlternativeIndices.append(index)
                index += 1

            if len(acceptedAlternativeTypes) == 0:
                return self.makeSemanticError(functional.sourcePosition, "No matching alternative for overloading function application.", functional, typedArgument)

            overloadedApplicationType = ASTOverloadsTypeNode(node.sourcePosition, acceptedAlternativeTypes)
            return reduceTypedOverloadedApplicationNode(ASTTypedOverloadedApplicationNode(node.sourcePosition, overloadedApplicationType, functional, acceptedAlternativeImplicitValueSubstitutions, typedArgument, acceptedAlternativeIndices))

        if not functionalType.isAnyFunctionTypeNode():
            functional = self.makeSemanticError(functional.sourcePosition, "Application functional must be a pi node, or it must have a forall or overloads type.", functional)
            return ASTTypedApplicationNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbsurdType), functional, self.visitNode(node.argument), [])
        
        pendingInferenceArgument, typedArgument, resultType, implicitValueSubstitutions, errorMessage = self.attemptBetaReducePiWithTypedArgument(functionalType, node.argument, isImplicitApplication = node.isImplicit)
        if errorMessage is not None:
            return self.makeSemanticError(node.sourcePosition, errorMessage, functional, typedArgument)
        
        if pendingInferenceArgument is not None:
            inferredApplication = ASTTypedApplicationNode(node.sourcePosition, resultType, functional, pendingInferenceArgument, implicitValueSubstitutions)
            nextApplication = ASTArgumentApplicationNode(node.sourcePosition, inferredApplication, typedArgument, isImplicit = node.isImplicit)
            return self.visitNode(nextApplication)

        return reduceTypedApplicationNode(ASTTypedApplicationNode(node.sourcePosition, resultType, functional, typedArgument, implicitValueSubstitutions))
    
    def visitImportModuleNode(self, node: ASTImportModuleNode):
        name, errorNode = self.evaluateSymbol(node.name)
        if errorNode is not None:
            return errorNode

        importedModule = self.lexicalEnvironment.lookModule().importModuleNamed(name)
        return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, importedModule.getType()), importedModule)

    def visitFromModuleImportWithTypeNode(self, node: ASTFromModuleImportWithTypeNode):
        module = self.visitNodeWithExpectedType(node.module, ModuleType)
        name, errorNode = self.evaluateSymbol(node.name)
        valueType = self.visitTypeExpression(node.type)
        if errorNode is not None:
            return self.visitNode(ASTSequenceNode(node.sourcePosition, [module, valueType, errorNode]))
        
        return reduceFromModuleImportNode(ASTTypedFromModuleImportNode(node.sourcePosition, valueType, module, name))

    def visitFromExternalImportWithTypeNode(self, node: ASTFromExternalImportWithTypeNode):
        externalName, externalErrorNode = self.evaluateSymbol(node.externalName)
        name, errorNode = self.evaluateSymbol(node.name)
        valueType = self.visitTypeExpression(node.type)
        errorList = []
        if externalErrorNode is not None:
            errorList.append(externalErrorNode)
        if errorNode is not None:
            errorList.append(errorNode)
        if len(errorList) != 0:
            return self.visitNode(ASTSequenceNode(node.sourcePosition, [valueType] + errorList))
        
        return reduceFromExternalImportNode(ASTTypedFromExternalImportWithTypeNode(node.sourcePosition, valueType, externalName, name))

    def visitModuleExportValueNode(self, node: ASTModuleExportValueNode):
        value = self.visitNode(node.value)

        externalName = None
        errorNodes = []
        if node.externalName is not None:
            externalName, errorNode = self.evaluateSymbol(node.externalName)
            if errorNode is not None:
                errorNodes.append(errorNode)

        name, errorNode = self.evaluateSymbol(node.name)
        if errorNode is not None:
            errorNodes.append(errorNode)

        if len(errorNodes) != 0:
            return self.visitNode(ASTSequenceNode(node.sourcePosition, [value] + errorNodes))
        
        return ASTTypedModuleExportValueNode(node.sourcePosition, value.type, externalName, name, value, self.lexicalEnvironment.lookModule())

    def visitModuleEntryPointNode(self, node: ASTModuleEntryPointNode):
        entryPoint = self.visitNode(node.entryPoint)
        entryPointType = getTypeOfAnalyzedNode(entryPoint, node.sourcePosition)
        if not entryPointType.isAnyFunctionTypeNode():
            return self.makeSemanticError(entryPoint.sourcePosition, "Module entry point must be a function.", entryPoint)
        return ASTTypedModuleEntryPointNode(node.sourcePosition, entryPointType, entryPoint, self.lexicalEnvironment.lookModule())

    def visitArgumentNode(self, node: ASTArgumentNode):
        assert False

    def visitBinaryExpressionSequenceNode(self, node: ASTBinaryExpressionSequenceNode):
        if len(node.elements) == 3:
            return self.visitNode(ASTMessageSendNode(node.sourcePosition, node.elements[0], node.elements[1], [node.elements[2]]))
        assert False

    def visitErrorNode(self, node: ASTErrorNode):
        errorNode = ASTTypedErrorNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbsurdType), node.message, [])
        self.errorAccumulator.add(errorNode)
        return errorNode

    def visitFunctionNode(self, node: ASTFunctionNode):
        if len(node.functionalType.arguments) == 0:
            return self.visitNode(ASTLambdaNode(node.sourcePosition, False, None, None, node.functionalType.resultType, node.body))

        resultType = node.functionalType.resultType
        body = node.body
        for argument in reversed(node.functionalType.arguments):
            body = ASTLambdaNode(argument.sourcePosition, argument.isImplicit, argument.typeExpression, argument.nameExpression, resultType, body)
            resultType = None
        return self.visitNode(body)
    
    def visitFunctionTypeNode(self, node: ASTFunctionTypeNode):
        argumentType = self.visitTypeExpression(node.argumentType)
        resultType = self.visitTypeExpression(node.resultType)
        typeUniverse = mergeTypeUniversesOfTypeNodes(argumentType, resultType, node.sourcePosition)
        return reduceFunctionTypeNode(ASTTypedFunctionTypeNode(node.sourcePosition, typeUniverse, argumentType, resultType))

    def visitFunctionalDependentTypeNode(self, node: ASTFunctionalDependentTypeNode):
        if len(node.arguments) == 0:
            return self.visitNode(ASTPiNode(node.sourcePosition, False, None, None, node.resultTypeExpression))

        resultType = node.resultType
        for argument in reversed(node.arguments):
            if argument.isExistential:
                resultType = ASTSigmaNode(argument.sourcePosition, argument.typeExpression, argument.nameExpression, resultType)
            else:
                resultType = ASTPiNode(argument.sourcePosition, argument.isImplicit, argument.typeExpression, argument.nameExpression, resultType)
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
            argumentType = ASTLiteralTypeNode(node.sourcePosition, UnitType)

        argumentBinding = SymbolArgumentBinding(node.sourcePosition, argumentName, argumentType, isImplicit = node.hasImplicitArgument)
        functionalEnvironment = FunctionalAnalysisEnvironment(self.lexicalEnvironment, argumentBinding, node.sourcePosition)
        body = self.withEnvironment(functionalEnvironment).visitNodeWithExpectedTypeExpression(node.body, node.resultType)

        ## Compute the lambda type.
        bodyType = getTypeOfAnalyzedNode(body, node.sourcePosition)
        typedPi = reducePiNode(ASTTypedPiNode(node.sourcePosition, mergeTypeUniversesOfTypeNodes(argumentType, bodyType, node.sourcePosition), argumentBinding, functionalEnvironment.captureBindings, bodyType))

        ## Make the lambda node.
        return reduceLambdaNode(ASTTypedLambdaNode(node.sourcePosition, typedPi, argumentBinding, functionalEnvironment.captureBindings, body))

    def visitPiNode(self, node: ASTPiNode):
        argumentName = self.evaluateOptionalSymbol(node.argumentName)
        argumentType = self.visitOptionalTypeExpression(node.argumentType)
        if argumentName is None and argumentType is None:
            argumentType = ASTLiteralTypeNode(UnitType)

        argumentBinding = SymbolArgumentBinding(node.sourcePosition, argumentName, argumentType, isImplicit = node.hasImplicitArgument)
        functionalEnvironment = FunctionalAnalysisEnvironment(self.lexicalEnvironment, argumentBinding, node.sourcePosition)
        body = self.withEnvironment(functionalEnvironment).visitTypeExpression(node.body)
        typedPi = ASTTypedPiNode(node.sourcePosition, mergeTypeUniversesOfTypeNodes(argumentType,  body, node.sourcePosition), argumentBinding, functionalEnvironment.captureBindings, body)
        return reducePiNode(typedPi)

    def visitSigmaNode(self, node: ASTSigmaNode):
        argumentName = self.evaluateOptionalSymbol(node.argumentName)
        argumentType = self.visitOptionalTypeExpression(node.argumentType)
        if argumentName is None and argumentType is None:
            argumentType = ASTLiteralTypeNode(UnitType)

        argumentBinding = SymbolArgumentBinding(node.sourcePosition, argumentName, argumentType)
        functionalEnvironment = FunctionalAnalysisEnvironment(self.lexicalEnvironment, argumentBinding, node.sourcePosition)
        body = self.withEnvironment(functionalEnvironment).visitTypeExpression(node.body)
        typedSigma = ASTTypedSigmaNode(node.sourcePosition, mergeTypeUniversesOfTypeNodes(argumentType,  body, node.sourcePosition), argumentBinding, functionalEnvironment.captureBindings, body)
        return reduceSigmaNode(typedSigma)

    def visitLexicalBlockNode(self, node: ASTLexicalBlockNode):
        innerEnvironment = LexicalEnvironment(self.lexicalEnvironment)
        return Typechecker(innerEnvironment, self.errorAccumulator).visitNode(node.expression)

    def visitLiteralNode(self, node: ASTLiteralNode):
        return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, node.value.getType()), node.value)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode):
        return node
    
    def visitBindingDefinitionNode(self, node: ASTBindingDefinitionNode):
        if node.initialValueExpression is None and node.expectedTypeExpression is None:
            return self.makeSemanticError(node.sourcePosition, "Local definition node requires at least an initial value or an expected type expression.")
        
        typecheckedValue = self.visitNodeWithExpectedTypeExpression(node.initialValueExpression, node.expectedTypeExpression)
        localName = self.evaluateOptionalSymbol(node.nameExpression)
        if localName is None:
            return typecheckedValue

        ## Make sure this is a correct place for a public binding
        if node.isPublic:
            if self.lexicalEnvironment.lookFunctionalAnalysisEnvironment() is not None:
                return self.makeSemanticError(node.sourcePosition, "Cannot have public bindings inside of functions..", typecheckedValue)
            module = self.lexicalEnvironment.lookModule()

        ## Use a symbol value binding if possible.
        module = None
        if typecheckedValue.isTypedLiteralNode() or typecheckedValue.isLiteralTypeNode():
            valueBinding = SymbolValueBinding(node.sourcePosition, localName, typecheckedValue.value)
            if node.isPublic:
                module.exportBinding(valueBinding)
            self.lexicalEnvironment = self.lexicalEnvironment.withSymbolBinding(valueBinding)
            return typecheckedValue
        
        ## Make a local variable.
        bindingTypeExpression = typecheckedValue.getTypeExpressionAt(node.sourcePosition)
        localBinding = SymbolLocalBinding(node.sourcePosition, localName, bindingTypeExpression, typecheckedValue)
        if node.isPublic:
            module.exportBinding(localBinding)
        self.lexicalEnvironment = self.lexicalEnvironment.withSymbolBinding(localBinding)
        return ASTTypedBindingDefinitionNode(node.sourcePosition, bindingTypeExpression, localBinding, typecheckedValue, isMutable = node.isMutable, isPublic = node.isPublic, module = module)

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
        expressionCount = len(node.elements)
        for i in range(expressionCount):
            expression = node.elements[i]
            typedExpression = self.visitNode(expression)
            if i + 1 < expressionCount and (typedExpression.isTypedLiteralNode() or typedExpression.isLiteralTypeNode()):
                continue

            resultType = typedExpression.type
            typedElements.append(typedExpression)

        if len(typedElements) == 1:
            return typedElements[0]
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
        return reduceTypedOverloadsNode(ASTTypedOverloadsNode(node.sourcePosition, overloadsType, typedAlternatives))

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

    def visitTypedFunctionTypeNode(self, node: ASTTypedFunctionTypeNode):
        return node

    def visitTypedPiNode(self, node: ASTTypedPiNode):
        return node

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode):
        return node

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode):
        return node

    def visitTypedImplicitValueNode(self, node):
        return node

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        return node

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        return node

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode):
        assert False

    def visitTypedOverloadedApplicationNode(self, node: ASTTypedOverloadedApplicationNode):
        return node

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode):
        return node

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode):
        return node

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        return node
    
    def visitTypedFromModuleImportNode(self, node: ASTTypedFromModuleImportNode):
        return node
    
    def visitTypedFromExternalImportWithTypeNode(self, node: ASTTypedFromExternalImportWithTypeNode):
        return node

    def visitTypedModuleExportValueNode(self, node: ASTTypedModuleExportValueNode):
        return node

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode):
        return node
    
    def loadSourceASTWithEnvironment(self, ast: ASTNode, scriptEnvironment: ScriptEnvironment, sourcePosition):
        scriptTypechecker = Typechecker(scriptEnvironment, self.errorAccumulator)
        hasErrorNodes = False
        errorVisitor = ASTErrorVisitor()
        errorVisitor.visitNode(ast)
        for errorNode in errorVisitor.errorNodes:
            scriptTypechecker.visitNode(errorNode)
            hasErrorNodes = True

        if hasErrorNodes:
            return self.makeSemanticError(sourcePosition, "Parse error when loading source file.", ast)
        return scriptTypechecker.visitNode(ast)

class SubstitutionContext:
    def __init__(self, parent = None) -> None:
        self.parent = parent
        self.bindingSubstitutionNodes = dict()
        self.bindingSubstitutionBindings = dict()
        self.localBindings = set()
        self.captureBindings = list()
        self.capturedBindingMap = dict()

    def addLocalBinding(self, binding: SymbolBinding):
        self.localBindings.add(binding)

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

    def lookSubstitutionForCapturedBindingInNode(self, binding: SymbolBinding) -> ASTTypedNode | ASTTypeNode | SymbolBinding:
        if binding in self.bindingSubstitutionNodes:
            return self.bindingSubstitutionNodes[binding]
        if binding in self.bindingSubstitutionBindings:
            return self.bindingSubstitutionBindings[binding]

        if self.parent is not None:
            return self.parent.lookSubstitutionForCapturedBindingInNode(binding)
        return None

    def addSubstitutionsForCaptureBindings(self, captureBindings: list[SymbolCaptureBinding]) -> None:
        for captureBinding in captureBindings:
            self.addSubstitutionForCaptureBinding(captureBinding)

    def addSubstitutionForCaptureBinding(self, captureBinding: SymbolCaptureBinding) -> None:
        if self.parent is None:
            return
        
        substitution = self.lookSubstitutionForCapturedBindingInNode(captureBinding.capturedBinding)
        if substitution is None:
            self.captureBindings.append(captureBinding)
            return

        if substitution.isSymbolBinding():
            if not substitution.isSymbolValueBinding():
                substitution = self.getOrCreateCaptureForBinding(substitution)

            self.bindingSubstitutionBindings[captureBinding] = substitution
        else:
            assert substitution.isASTNode()
            ASTCaptureBindingFinder(self).visitNode(substitution)
            self.bindingSubstitutionNodes[captureBinding] = substitution

    def getOrCreateCaptureForBinding(self, binding: SymbolBinding) -> SymbolCaptureBinding:
        if binding.isValueBinding(): return binding
        if binding in self.capturedBindingMap:
            return self.capturedBindingMap[binding]
        
        capturedBinding = SymbolCaptureBinding(binding.sourcePosition, binding.name, binding)
        self.capturedBindingMap[binding] = capturedBinding
        self.captureBindings.append(capturedBinding)
        return capturedBinding

    def setSubstitutionNodeForBinding(self, binding: SymbolBinding, substitution: ASTTypedNode | ASTTypeNode) -> None:
        self.bindingSubstitutionNodes[binding] = substitution

    def setSubstitutionBindingForBinding(self, binding: SymbolBinding, newBinding: SymbolBinding) -> None:
        self.bindingSubstitutionBindings[binding] = newBinding

    def applySourcePositionToSubstitution(self, substitution: ASTNode, sourcePosition: SourcePosition) -> ASTNode:
        if substitution.isTypedIdentifierReferenceNode():
            return ASTTypedIdentifierReferenceNode(sourcePosition, substitution.type, substitution.binding)
        return substitution

class ASTCaptureBindingFinder(ASTSequentialVisitor):
    def __init__(self, context) -> None:
        super().__init__()
        self.context = context

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode):
        self.visitNode(node.valueExpression)
        self.context.addLocalBinding(node.binding)

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode):
        self.context.getOrCreateCaptureForBinding(node.binding)

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        self.visitNode(node.type)
        self.visitNode(node.argumentBinding.typeExpression)
        for captureBinding in node.captureBindings:
            self.context.getOrCreateCaptureForBinding(captureBinding.capturedBinding)

    def visitTypedPiNode(self, node: ASTTypedPiNode):
        self.visitNode(node.type)
        self.visitNode(node.argumentBinding.typeExpression)
        for captureBinding in node.captureBindings:
            self.context.getOrCreateCaptureForBinding(captureBinding.capturedBinding)
    
class ASTBetaReducer(ASTTypecheckedVisitor):
    def __init__(self, substitutionContext: SubstitutionContext) -> None:
        super().__init__()
        self.substitutionContext = substitutionContext

    def visitNode(self, node: ASTNode) -> ASTTypedNode | ASTTypeNode:
        return node.accept(self)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode) -> ASTLiteralTypeNode:
        return node
    
    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        for binding, substitution in node.implicitValueSubstitutions:
            self.substitutionContext.setSubstitutionNodeForBinding(binding, self.visitNode(substitution))

        return reduceTypedApplicationNode(ASTTypedApplicationNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.functional), self.visitNode(node.argument), []))

    def visitTypedErrorNode(self, node: ASTTypedErrorNode):
        return node

    def visitTypedFunctionTypeNode(self, node: ASTTypedFunctionTypeNode):
        newType = self.visitNode(node.type)
        argumentType = self.visitNode(node.argumentType)
        resultType = self.visitNode(node.resultType)
        return reduceFunctionTypeNode(ASTTypedFunctionTypeNode(node.sourcePosition, newType, argumentType, resultType))

    def visitTypedPiNode(self, node: ASTTypedPiNode):
        argumentBinding = node.argumentBinding
        newArgumentBinding = SymbolArgumentBinding(argumentBinding.sourcePosition, argumentBinding.name, self.visitNode(argumentBinding.typeExpression))
        newType = self.visitNode(node.type)

        bodyContext = SubstitutionContext(self.substitutionContext)
        bodyContext.setSubstitutionBindingForBinding(argumentBinding, newArgumentBinding)
        bodyContext.addSubstitutionsForCaptureBindings(node.captureBindings)

        reducedBody = ASTBetaReducer(bodyContext).visitNode(node.body)
        return reducePiNode(ASTTypedPiNode(node.sourcePosition, newType, newArgumentBinding, bodyContext.captureBindings, reducedBody))

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode):
        return node.binding.evaluateSubstitutionInContextFor(self.substitutionContext, node)

    def visitTypedImplicitValueNode(self, node):
        return node
    
    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        argumentBinding = node.argumentBinding
        newArgumentBinding = SymbolArgumentBinding(argumentBinding.sourcePosition, argumentBinding.name, self.visitNode(argumentBinding.typeExpression))
        newType = self.visitNode(node.type)
        
        bodyContext = SubstitutionContext(self.substitutionContext)
        bodyContext.setSubstitutionBindingForBinding(argumentBinding, newArgumentBinding)
        bodyContext.addSubstitutionsForCaptureBindings(node.captureBindings)

        reducedBody = ASTBetaReducer(bodyContext).visitNode(node.body)
        return reduceLambdaNode(ASTTypedLambdaNode(node.sourcePosition, newType, newArgumentBinding, bodyContext.captureBindings, reducedBody))

    def visitTypedSigmaNode(self, node: ASTTypedLambdaNode):
        argumentBinding = node.argumentBinding
        newArgumentBinding = SymbolArgumentBinding(argumentBinding.sourcePosition, argumentBinding.name, self.visitNode(argumentBinding.typeExpression))
        newType = self.visitNode(node.type)
        
        bodyContext = SubstitutionContext(self.substitutionContext)
        bodyContext.setSubstitutionBindingForBinding(argumentBinding, newArgumentBinding)
        bodyContext.addSubstitutionsForCaptureBindings(node.captureBindings)

        reducedBody = ASTBetaReducer(bodyContext).visitNode(node.body)
        return reduceSigmaNode(ASTTypedSigmaNode(node.sourcePosition, newType, newArgumentBinding, bodyContext.captureBindings, reducedBody))

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        return node

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode):
        assert False

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

    def visitTypedOverloadedApplicationNode(self, node: ASTTypedOverloadedApplicationNode):
        for alternativeImplicitValueSubstitutions in node.alternativeImplicitValueSubstitutions:
            for binding, substitution in alternativeImplicitValueSubstitutions:
                self.substitutionContext.setSubstitutionNodeForBinding(binding, self.visitNode(substitution))

        overloads = self.visitNode(node.overloads)
        argument = self.visitNode(node.argument)
        applicationType = self.visitNode(node.type)
        return ASTTypedOverloadedApplicationNode(node.sourcePosition, applicationType, overloads, argument, node.alternativeIndices)
    
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
    
    def visitTypedFromModuleImportNode(self, node: ASTTypedFromModuleImportNode):
        return reduceFromModuleImportNode(ASTTypedFromModuleImportNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.module), node.name))

    def visitTypedModuleExportValueNode(self, node: ASTTypedModuleExportValueNode):
        return ASTTypedModuleExportValueNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.value))

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode):
        return ASTTypedModuleEntryPointNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.entryPoint))
    
def getTypeOfAnalyzedNode(node: ASTTypedNode | ASTTypeNode, sourcePosition: SourcePosition) -> ASTTypedNode | ASTTypeNode:
    if node.isTypeNode():
        return ASTLiteralTypeNode(sourcePosition, node.getTypeUniverse())
    return node.type

def betaReduceFunctionalNodeWithArgument(functionalNode: ASTTypedNode | ASTTypeNode, argument: ASTTypedNode | ASTTypeNode):
    if functionalNode.isTypedFunctionalNode():
        typedFunctionalNode: ASTTypedFunctionalNode = functionalNode
        argumentBinding = typedFunctionalNode.argumentBinding
        body = typedFunctionalNode.body

        assert len(typedFunctionalNode.captureBindings) == 0

        substitutionContext = SubstitutionContext()
        substitutionContext.setSubstitutionNodeForBinding(argumentBinding, argument)
    else:
        assert functionalNode.isTypedLiteralNode() or functionalNode.isLiteralTypeNode()
        functionalValue: FunctionalValue = functionalNode.value
        argumentBinding = functionalValue.argumentBinding
        body = functionalValue.body
        assert len(functionalValue.captureBindings) == 0

        substitutionContext = SubstitutionContext()
        substitutionContext.setSubstitutionNodeForBinding(argumentBinding, argument)
    return ASTBetaReducer(substitutionContext).visitNode(body)
    
def makeTypedLiteralForValueAt(value: TypedValue, sourcePosition: SourcePosition) -> ASTTypedLiteralNode | ASTTypeNode:
    if value.isType():
        return ASTLiteralTypeNode(sourcePosition, value)
    return ASTTypedLiteralNode(sourcePosition, ASTLiteralTypeNode(sourcePosition, value.getType()), value)

def reduceTypedApplicationNode(node: ASTTypedApplicationNode):
    if len(node.implicitValueSubstitutions) != 0:
        return ASTBetaReducer(SubstitutionContext()).visitNode(node)

    hasTypeArgument = node.argument.isTypeNode()
    hasLiteralArgument = node.argument.isLiteralTypeNode() or node.argument.isTypedLiteralNode()
    hasLiteralFunctionalNode = node.functional.isLiteralTypeNode() or node.functional.isTypedLiteralNode()
    hasBetaReducibleFunctional = node.functional.isTypedLambdaNode() or node.functional.isTypedPiNode() or node.functional.isTypedLiteralReducibleFunctionalValue()

    if hasLiteralFunctionalNode and node.functional.value.isPurelyFunctional() and hasLiteralArgument:
        return makeTypedLiteralForValueAt(node.functional.value(node.argument.value), node.sourcePosition)

    if hasTypeArgument and hasBetaReducibleFunctional:
        return betaReduceFunctionalNodeWithArgument(node.functional, node.argument)

    return node

def reduceTypedOverloadedApplicationNode(node: ASTTypedOverloadedApplicationNode):
    assert node.type.isOverloadsTypeNode()
    if node.overloads.isTypedOverloadsNode():
        overloadsNode: ASTTypedOverloadsNode = node.overloads
        resultOverloadsType: ASTOverloadsTypeNode = node.type

        assert len(resultOverloadsType.alternativeTypes) >= 0
        assert len(resultOverloadsType.alternativeTypes) == len(node.alternativeIndices)
        alternativesWithApplication = []
        for i in range(len(resultOverloadsType.alternativeTypes)):
            alternative = overloadsNode.alternatives[node.alternativeIndices[i]]
            implicitValueSubstitutions = node.alternativeImplicitValueSubstitutions[i]
            resultType = resultOverloadsType.alternativeTypes[i]
            alternativesWithApplication.append(reduceTypedApplicationNode(ASTTypedApplicationNode(node.sourcePosition, resultType, alternative, node.argument, implicitValueSubstitutions)))
        return reduceTypedOverloadsNode(ASTTypedOverloadsNode(node.sourcePosition, node.type, alternativesWithApplication))
    return node

def isLiteralTypeOfTypeNode(node: ASTNode):
    return (node.isLiteralTypeNode() or node.isTypedLiteralNode()) and node.value.isTypeUniverse()

def isMacroValueNode(node: ASTNode):
    return node.isTypedLiteralNode() and node.value.isMacroValue()

def reduceType(node: ASTNode):
    if node.isTypedLiteralNode() and isLiteralTypeOfTypeNode(node.type):
        return ASTLiteralTypeNode(node.sourcePosition, node.value)

    return node

def reduceFunctionTypeNode(node: ASTTypedFunctionTypeNode):
    if node.argumentType.isLiteralTypeNode() and node.resultType.isLiteralTypeNode():
        functionType = FunctionType.makeFromTo(node.argumentType.value, node.resultType.value)
        return ASTLiteralTypeNode(node.sourcePosition, functionType)
    return node

def reducePiNode(node: ASTTypedPiNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        piValue = PiValue(node.type.value, node.argumentBinding, [], [], node.body, node.sourcePosition)
        return ASTLiteralTypeNode(node.sourcePosition, piValue)
    return node

def reduceSigmaNode(node: ASTTypedPiNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        sigmaValue = SigmaValue(node.type.value, node.argumentBinding, [], [], node.body, node.sourcePosition)
        return ASTLiteralTypeNode(node.sourcePosition, sigmaValue)
    return node

def reduceLambdaNode(node: ASTTypedLambdaNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        lambdaValue = LambdaValue(node.type.value, node.argumentBinding, [], [], node.body, node.sourcePosition)
        return ASTTypedLiteralNode(node.sourcePosition, node.type, lambdaValue)
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

def reduceFromModuleImportNode(node: ASTTypedFromModuleImportNode):
    if node.module.isTypedLiteralNode() and node.type.isLiteralTypeNode():
        module: ImportedModule = node.module.value
        type: TypedValue = node.type.value
        importedValue = module.importValueWithType(node.name, type)
        return ASTTypedLiteralNode(node.sourcePosition, type, importedValue)
    return node

def reduceFromExternalImportNode(node: ASTTypedFromExternalImportWithTypeNode):
    if node.type.isLiteralTypeNode():
        type: TypedValue = node.type.value
        importedValue = ImportedExternalValue(node.externalName, node.name, type)
        return ASTTypedLiteralNode(node.sourcePosition, type, importedValue)
    return node

def reduceSumTypeNode(node: ASTSumTypeNode):
    if len(node.alternativeTypes) == 0:
        return ASTLiteralTypeNode(node.sourcePosition, AbsurdType)
    elif len(node.alternativeTypes) == 1:
        return node.alternativeTypes[0]
    return node

def mergeTypeUniversesOfTypeNodes(leftNode: ASTTypedNode, rightNode: ASTTypedNode, sourcePosition: SourcePosition) -> ASTLiteralTypeNode:
    leftUniverseIndex = leftNode.computeTypeUniverseIndex()
    rightUniverseIndex = rightNode.computeTypeUniverseIndex()
    mergedUniverse = max(leftUniverseIndex, rightUniverseIndex)
    return ASTLiteralTypeNode(sourcePosition, TypeUniverse.getWithIndex(mergedUniverse))
