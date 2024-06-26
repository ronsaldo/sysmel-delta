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
            print('%s: error: %s' % (error.sourcePosition, error.message))
        return False

class Typechecker(ASTVisitor):
    def __init__(self, lexicalEnvironment: LexicalEnvironment, errorAccumulator: ErrorAccumulator = None):
        self.lexicalEnvironment = lexicalEnvironment
        self.errorAccumulator = errorAccumulator
        if self.errorAccumulator is None:
            self.errorAccumulator = ErrorAccumulator()

    def withEnvironment(self, newEnvironment: LexicalEnvironment):
        return Typechecker(newEnvironment, self.errorAccumulator)

    def visitNode(self, node: ASTNode) -> ASTNode:
        return node.accept(self)

    def visitNodeWithExpectedTypeExpression(self, node: ASTNode, expectedTypeExpression: ASTNode) -> ASTNode:
        if expectedTypeExpression is None:
            return self.visitNode(node)

        typedNode = self.visitNode(node)
        expectedTypeNode = self.visitTypeExpression(expectedTypeExpression)
        typedNode = self.applyCoercionsToNodeFor(typedNode, expectedTypeNode)
        typedNodeType = getTypeOfAnalyzedNode(typedNode, typedNode.sourcePosition)
        if typedNodeType != expectedTypeNode and not typedNodeType.isEquivalentTo(expectedTypeNode):
            return self.makeSemanticError(node.sourcePosition, "Type checking failure. Value has type '%s' instead of expected type of '%s'." % (typedNodeType.prettyPrint(), expectedTypeNode.prettyPrint()), typedNode, expectedTypeNode)
        return typedNode
    
    def visitNodeWithCurrentExpectedType(self, node: ASTNode) -> ASTNode:
        return self.visitNode(node)
    
    def mergeTypesOfBranch(self, leftTypeExpression: ASTNode, rightTypeExpression: ASTNode, sourcePosition: SourcePosition):
        if leftTypeExpression.isEquivalentTo(rightTypeExpression):
            return leftTypeExpression

        return self.makeSemanticError(sourcePosition, "Type checking failure. Branch has mismatching types. '%s' vs '%s'" % (leftTypeExpression.prettyPrint(), rightTypeExpression.prettyPrint()))

    def mergeListOfTypes(self, typeExpressions: list[ASTNode], defaultTypeExpression: ASTNode, sourcePosition: SourcePosition):
        if len(typeExpressions) == 0:
            return defaultTypeExpression
        
        mergedTypeExpression = typeExpressions[0]
        for i in range(1, len(typeExpressions)):
            typeExpression = typeExpressions[i]
            mergedTypeExpression = self.mergeTypesOfBranch(mergedTypeExpression, typeExpression, sourcePosition)
        return mergedTypeExpression

    def applyCoercionsToNodeFor(self, node: ASTNode, targetTypeExpression: ASTTypeNode):
        nodeType = getTypeOfAnalyzedNode(node, node.sourcePosition)
        if targetTypeExpression.isProductTypeNodeOrLiteral():
            unpackedArgument = node.attemptToUnpackTupleExpressionsAt(node.sourcePosition)
            if unpackedArgument is not None:
                unpackedTupleTypeElements = targetTypeExpression.asUnpackedTupleTypeExpressionsAt(node.sourcePosition)
                if len(unpackedArgument) == len(unpackedTupleTypeElements):
                    coercedTupleElements = []
                    hasDoneCoercion = False
                    for i in range(len(unpackedArgument)):
                        coercedElement = self.applyCoercionsToNodeFor(unpackedArgument[i], unpackedTupleTypeElements[i])
                        hasDoneCoercion = hasDoneCoercion or (coercedElement is not unpackedArgument[i])
                        coercedTupleElements.append(coercedElement)

                    if hasDoneCoercion:
                       coercedNode = self.visitNode(ASTTupleNode(node.sourcePosition, coercedTupleElements))
                       return self.applyCoercionsToNodeFor(coercedNode, targetTypeExpression)

        if targetTypeExpression.isSumTypeNodeOrLiteral():
            injectionIndexOrNode = targetTypeExpression.findIndexOfSumVariantOrNoneAt(nodeType, node.sourcePosition)
            if injectionIndexOrNode is not None:
                return reduceInjectSumNode(ASTTypedInjectSumNode(node.sourcePosition, targetTypeExpression, injectionIndexOrNode, node))

        if not targetTypeExpression.isReferenceLikeTypeNodeOrLiteral() and nodeType.isReferenceLikeTypeNodeOrLiteral():
            coercedNode = self.visitNode(ASTPointerLikeLoadNode(node.sourcePosition, node))
            return self.applyCoercionsToNodeFor(coercedNode, targetTypeExpression)
        
        if targetTypeExpression.isCVarArgTypeNode():
            return self.visitNode(nodeType.applyCoercionExpresionIntoCVarArgType(node))

        return node

    def attemptToVisitNodeWithExpectedTypeExpression(self, node: ASTNode, expectedTypeExpression: ASTNode, startingImplicitValueSubstitutions = []) -> tuple[tuple[SymbolImplicitValueBinding, ASTNode], ASTNode, str]:
        typedNode = self.visitNode(node)

        if expectedTypeExpression is None:
            return [], typedNode, None

        expectedTypeNode = self.visitTypeExpression(expectedTypeExpression)
        coercedTypedNode = self.applyCoercionsToNodeFor(typedNode, expectedTypeNode)
        startingEnvironment = self.lexicalEnvironment
        doesTypeCheck, newEnvironment = self.withEnvironment(self.lexicalEnvironment.withImplicitValueBindingSubstitutions(startingImplicitValueSubstitutions)).doesTypedNodeConformToTypeExpression(coercedTypedNode, expectedTypeNode)
        implicitValueSubstitutions = newEnvironment.getImplicitValueSubstitutionsUpTo(startingEnvironment)
        if not doesTypeCheck:
            return implicitValueSubstitutions, coercedTypedNode, "Type checking failure. Value has type '%s' instead of expected type of '%s'." % (getTypeOfAnalyzedNode(typedNode, typedNode.sourcePosition).prettyPrint(), expectedTypeNode.prettyPrint())
        
        return implicitValueSubstitutions, coercedTypedNode, None
    
    def attemptToVisitNodeWithExpectedType(self, node: ASTNode, expectedType: TypedValue) -> tuple[ASTNode, str]:
        return self.attemptToVisitNodeWithExpectedTypeExpression(node, ASTLiteralTypeNode(node.sourcePosition, expectedType))

    def doesTypedNodeConformToTypeExpression(self, typedNode: ASTNode, expectedTypeExpression: ASTNode) -> ASTNode:
        typedNodeType = getTypeOfAnalyzedNode(typedNode, typedNode.sourcePosition)
        expectedTypeNode = self.visitTypeExpression(expectedTypeExpression)
        return expectedTypeNode.performSatisfiedByCheckInEnvironment(typedNodeType, self.lexicalEnvironment)
    
    def visitNodeWithExpectedType(self, node: ASTNode, expectedType: TypedValue) -> ASTNode:
        if expectedType is None:
            return self.visitNode(node)

        return self.visitNodeWithExpectedTypeExpression(node, ASTLiteralTypeNode(node.sourcePosition, expectedType))
    
    def visitNodeForMacroExpansionOnly(self, node: ASTNode) -> ASTNode:
        if node.isMessageSendNode():
            messageSend: ASTMessageSendNode = node
            selector, errorNode = self.evaluateSymbol(messageSend.selector)
            if errorNode is not None:
                return node

            bindings = self.lexicalEnvironment.lookSymbolBindingListRecursively(selector)
            for binding in bindings:
                if not binding.isValueBinding():
                    continue
                bindingValue = binding.value
                if bindingValue.isMacroValue():
                    macroValue = bindingValue
                    applicationArguments = []
                    if macroValue.expectsMacroEvaluationContext():
                        applicationArguments = [MacroContext(node.sourcePosition, self.lexicalEnvironment, self)]

                    if messageSend.receiver is not None:
                        applicationArguments.append(messageSend.receiver)
                    applicationArguments += messageSend.arguments

                    macroValue = macroValue(*applicationArguments)
                    if not macroValue.isASTNode():
                        return self.makeSemanticError(node.sourcePosition, "Macro expansion does not complete into an AST node.")
                    
                    return self.visitNodeForMacroExpansionOnly(macroValue)
        return node

    def evaluateSymbol(self, node: ASTNode) -> Symbol:
        return self.evaluateReducedLiteral(self.visitNodeWithExpectedType(node, SymbolType))

    def evaluateString(self, node: ASTNode) -> Symbol:
        return self.evaluateReducedLiteral(self.visitNodeWithExpectedType(node, StringType))

    def evaluateInteger(self, node: ASTNode) -> Symbol:
        return self.evaluateReducedLiteral(self.visitNodeWithExpectedType(node, IntegerType))

    def evaluateOptionalSymbol(self, node: ASTNode) -> Symbol:
        if node is None:
            return None
        
        symbol, errorNode = self.evaluateSymbol(node)
        return symbol
    
    def evaluateReducedLiteral(self, node: ASTTypedNode) -> TypedValue:
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
            return ASTLiteralTypeNode(node.sourcePosition, AbortType)

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
        errorNode = ASTTypedErrorNode(sourcePosition, ASTLiteralTypeNode(sourcePosition, AbortType), errorMessage, innerNodes)
        self.errorAccumulator.add(errorNode)
        return errorNode
    
    def expandDictionaryApplicationNode(self, node: ASTApplicationNode):
        assert len(node.arguments) == 1
        functional = self.visitNode(node.functional)
        if functional.isRecordTypeNodeOrLiteral():
            keys, values, errorNode = self.expandAndUnpackUnzippedDictionaryNodeWithElements(node.arguments[0])
            assert errorNode is None
            return self.visitNode(ASTRecordNode(node.sourcePosition, functional, keys, values))
        
        functionalType = getTypeOfAnalyzedNode(functional, node.sourcePosition)
        if functionalType.isRecordTypeNodeOrLiteral():
            keys, values, errorNode = self.expandAndUnpackUnzippedDictionaryNodeWithElements(node.arguments[0])
            assert errorNode is None
            return self.visitNode(ASTModifiedRecordNode(node.sourcePosition, functional, keys, values))

        selector = ASTLiteralNode(node.sourcePosition, Symbol.intern('#{}:'))
        return self.visitNode(ASTMessageSendNode(node.sourcePosition, functional, selector, node.arguments))

    def visitApplicationNode(self, node: ASTApplicationNode):
        if node.kind == ASTApplicationNode.Bracket:
            return self.visitNode(ASTMessageSendNode(node.sourcePosition, node.functional, ASTLiteralNode(node.sourcePosition, Symbol.intern('[]:')), node.arguments))
        elif node.kind == ASTApplicationNode.CurlyBracket:
            return self.visitNode(ASTMessageSendNode(node.sourcePosition, node.functional, ASTLiteralNode(node.sourcePosition, Symbol.intern('{}:')), node.arguments))
        elif node.kind == ASTApplicationNode.Dictionary:
            return self.expandDictionaryApplicationNode(node)

        functional = self.visitNode(node.functional)
        isImplicit = node.kind == ASTApplicationNode.ByteArrayStart

        if len(node.arguments) == 0:
            return self.visitNode(ASTArgumentApplicationNode(node.sourcePosition, functional, ASTLiteralNode(node.sourcePosition, VoidType.getSingleton()), isImplicit = isImplicit))

        for argument in node.arguments:
            functional = self.visitNode(ASTArgumentApplicationNode(argument.sourcePosition, functional, argument, isImplicit = isImplicit))
        return functional
    
    def unpackArgumentsToRequiredArity(self, argument: ASTNode, declaredArity: int, isVariadic: bool):
        minimalArity = declaredArity
        if isVariadic:
            minimalArity -= 1

        assert minimalArity >= 0
        assert declaredArity >= 1

        if not isVariadic and declaredArity == 1:
            return [argument], None

        if argument.isTupleNode() or argument.isTypedTupleNode():
            argumentArity = len(argument.elements)
            if isVariadic and argumentArity < minimalArity:
                return None, "Expected at least %d arguments instead of %d." % (minimalArity, argumentArity)
            elif not isVariadic and argumentArity != declaredArity:
                return None, "Expected %d arguments instead of %d." % (declaredArity, argumentArity)
            return argument.elements, None
        
        if isVariadic and minimalArity <= 1:
            return [argument], None

        assert False

    def packArguments(self, arguments: list[ASTTypedNode], sourcePosition: SourcePosition):
        if len(arguments) == 0:
            return self.visitNode(ASTLiteralNode(sourcePosition), VoidType.getSingleton())
        elif len(arguments) == 1:
            return arguments[0]
        return self.visitNode(ASTTupleNode(sourcePosition, arguments))

    def attemptBetaReducePiWithTypedArgument(self, piNode: ASTNode, argument: ASTNode, isImplicitApplication = False):
        substitutionContext = SubstitutionContext()
        if piNode.isFunctionTypeLiteralValue():
            functionType: FunctionType = piNode.value
            if isImplicitApplication:
                return [], self.visitNode(argument), None, [], "Unexpected implicit argument application, when an explicit argument of type %s is required." % functionType.resultType.prettyPrint()
            
            implicitValueSubstitutions, typedArgument, errorMessage = self.attemptToVisitNodeWithExpectedType(argument, functionType.argumentType)
            if errorMessage is not None:
                return [], typedArgument, None, implicitValueSubstitutions, errorMessage

            resultTypeNode = ASTLiteralTypeNode(argument.sourcePosition, functionType.resultType)
            return [], typedArgument, resultTypeNode, implicitValueSubstitutions, None
        
        elif piNode.isTypedFunctionTypeNode():
            assert False
        elif piNode.isPiLiteralValue():
            piValue: FunctionalValue = piNode.value
            argumentBindings = piValue.argumentBindings
            piBody = piValue.body
            isVariadic = piValue.isVariadic
        else:
            assert piNode.isTypedPiNode()
            typedFunctionalNode: ASTTypedFunctionalNode = piNode
            argumentBindings = list(map(lambda n: n.binding, typedFunctionalNode.arguments))
            piBody = typedFunctionalNode.body
            isVariadic = typedFunctionalNode.isVariadic

        ## If there are zero arguments, the argument must be unit.
        if len(argumentBindings) == 0:
            implicitValueSubstitutions, typedArgument, errorMessage = self.attemptToVisitNodeWithExpectedType(argument, VoidType)
            if errorMessage is not None:
                return [], typedArgument, None, implicitValueSubstitutions, errorMessage
            return piBody

        firstArgumentBinding = argumentBindings[0]
        if isImplicitApplication and not firstArgumentBinding.isImplicit:
            return [], self.visitNode(argument), None, [], "Unexpected implicit argument application, when an explicit argument of type %s is required." % firstArgumentBinding.getTypeExpression().prettyPrint()
        
        ## Are we missing implicit arguments that need to be inferred?
        if firstArgumentBinding.isImplicit and not isImplicitApplication:
            reducer = ASTBetaReducer(substitutionContext)
            implicitArgumentValueNodes = []

            for argumentBinding in argumentBindings:
                assert argumentBinding.isImplicit
                argumentTypeExpression = reducer.visitNode(argumentBinding.getTypeExpression())
                placeHolderBinding = SymbolImplicitValueBinding(argument.sourcePosition, argumentBinding.name, argumentTypeExpression)
                implicitArgumentValueNode = ASTTypedIdentifierReferenceNode(argument.sourcePosition, placeHolderBinding.typeExpression, placeHolderBinding)
                implicitArgumentValueNodes.append(implicitArgumentValueNode)

                substitutionContext.setSubstitutionNodeForBinding(argumentBinding, implicitArgumentValueNode)

            reduced = ASTBetaReducer(substitutionContext).visitNode(piBody)
            return implicitArgumentValueNodes, argument, reduced, [], None
        
        unpackedArguments, errorMessage = self.unpackArgumentsToRequiredArity(argument, len(argumentBindings), isVariadic)
        if errorMessage is not None:
            return [], [argument], None, [], errorMessage

        implicitValueSubstitutions = []
        unpackedTypedArguments = []
        for i in range(len(unpackedArguments)):
            argumentBinding = argumentBindings[min(i, len(argumentBindings) - 1)]
            implicitValueSubstitutions, unpackedTypedArgument, errorMessage = self.attemptToVisitNodeWithExpectedTypeExpression(unpackedArguments[i], argumentBinding.getTypeExpression(), implicitValueSubstitutions)
            if errorMessage is not None:
                return [], unpackedTypedArgument, None, implicitValueSubstitutions, errorMessage

            substitutionContext.setSubstitutionNodeForBinding(argumentBinding, unpackedTypedArgument)
            unpackedTypedArguments.append(unpackedTypedArgument)

        reduced = ASTBetaReducer(substitutionContext).visitNode(piBody)
        return [], self.packArguments(unpackedTypedArguments, argument.sourcePosition), reduced, implicitValueSubstitutions, errorMessage
    
    def unpackArgumentsForMacro(self, macroValue: TypedValue, node: ASTNode, sourcePosition: SourcePosition):
        macroType = macroValue.getType()
        if not macroType.argumentType.isProductType():
            return [node], None
        
        requiredArity = len(macroType.argumentType.elementTypes)
        if macroValue.expectsMacroEvaluationContext():
            requiredArity -= 1

        if requiredArity == 0:
            return [], None
        elif requiredArity == 1:
            if node.isTupleNode() or node.isTypedTupleNode() and len(node.elements) == 1:
                return node.elements, None
            return [node], None
        
        if node.isTupleNode() or node.isTypedTupleNode():
            return node.elements, None

        return None, "Macro requires %d arguments instead of one." % requiredArity

    def visitArgumentApplicationNode(self, node: ASTArgumentApplicationNode):
        functional = self.visitNode(node.functional)
        if functional.isTypedErrorNode():
            return ASTTypedApplicationNode(node.sourcePosition, functional.type, functional, self.visitNode(node.argument), [])
        
        if isMacroValueNode(functional):
            macroValue = functional.value
            applicationArguments = []
            if macroValue.expectsMacroEvaluationContext():
                applicationArguments = [MacroContext(node.sourcePosition, self.lexicalEnvironment, self)]
            unpackedArguments, errorMessage = self.unpackArgumentsForMacro(macroValue, node.argument, node.sourcePosition)
            if errorMessage is not None:
                return self.makeSemanticError(node.sourcePosition, errorMessage, functional, node.argument)

            applicationArguments = applicationArguments + unpackedArguments
            macroEvaluationResult = macroValue(*applicationArguments)

            if macroEvaluationResult.isMacroValue():
                return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, macroEvaluationResult.getType()), macroEvaluationResult)
            assert isinstance(macroEvaluationResult, ASTNode)
            return self.visitNode(macroEvaluationResult)

        if functional.isAnyFunctionTypeNode():
            pendingInferenceArguments, typedArgument, resultType, implicitValueSubstitutions, errorMessage = self.attemptBetaReducePiWithTypedArgument(functional, node.argument, isImplicitApplication = node.isImplicit)
            if errorMessage is not None:
                return self.makeSemanticError(node.sourcePosition, errorMessage, functional, typedArgument)

            assert len(pendingInferenceArguments) == 0
            return resultType
        
        functionalType = getTypeOfAnalyzedNode(functional, node.sourcePosition)
        if functionalType.isOverloadsTypeNode():
            acceptedAlternativeTypes = []
            acceptedAlternativeIndices = []
            acceptedAlternativeTypedArguments = []
            acceptedAlternativeImplicitValueSubstitutions = []
            index = 0
            typedArgument = self.visitNode(node.argument)
            for alternativeType in functional.type.alternativeTypes:
                pendingInferenceArguments, alternativeTypedArgument, resultType, implicitValueSubstitutions, errorMessage = self.attemptBetaReducePiWithTypedArgument(alternativeType, typedArgument, isImplicitApplication = node.isImplicit)
                assert len(pendingInferenceArguments) == 0
                if errorMessage is None:
                    acceptedAlternativeImplicitValueSubstitutions.append(implicitValueSubstitutions)

                    acceptedAlternativeTypes.append(resultType)
                    acceptedAlternativeTypedArguments.append(alternativeTypedArgument)
                    acceptedAlternativeIndices.append(index)
                index += 1

            if len(acceptedAlternativeTypes) == 0:
                return self.makeSemanticError(functional.sourcePosition, "No matching alternative for overloading function application.", functional, typedArgument)

            overloadedApplicationType = ASTOverloadsTypeNode(node.sourcePosition, acceptedAlternativeTypes)
            return reduceTypedOverloadedApplicationNode(ASTTypedOverloadedApplicationNode(node.sourcePosition, overloadedApplicationType, functional, acceptedAlternativeImplicitValueSubstitutions, acceptedAlternativeTypedArguments, acceptedAlternativeIndices))

        if not functionalType.isAnyFunctionTypeNode():
            functional = self.makeSemanticError(functional.sourcePosition, "Application functional must be a pi node, or it must have a forall or overloads type.", functional)
            return ASTTypedApplicationNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbortType), functional, self.visitNode(node.argument), [])
        
        pendingInferenceArguments, typedArgument, resultType, implicitValueSubstitutions, errorMessage = self.attemptBetaReducePiWithTypedArgument(functionalType, node.argument, isImplicitApplication = node.isImplicit)
        if errorMessage is not None:
            return self.makeSemanticError(node.sourcePosition, errorMessage, functional, typedArgument)
        
        if len(pendingInferenceArguments) != 0:
            inferredApplication = ASTTypedApplicationNode(node.sourcePosition, resultType, functional, self.packArguments(pendingInferenceArguments, node.sourcePosition), implicitValueSubstitutions)
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
        
        valueType = getTypeOfAnalyzedNode(value, node.sourcePosition)
        return ASTTypedModuleExportValueNode(node.sourcePosition, valueType, externalName, name, value, self.lexicalEnvironment.lookModule())

    def visitModuleEntryPointNode(self, node: ASTModuleEntryPointNode):
        entryPoint = self.visitNode(node.entryPoint)
        entryPointType = getTypeOfAnalyzedNode(entryPoint, node.sourcePosition)
        if not entryPointType.isAnyFunctionTypeNode():
            return self.makeSemanticError(entryPoint.sourcePosition, "Module entry point must be a function.", entryPoint)
        return ASTTypedModuleEntryPointNode(node.sourcePosition, entryPointType, entryPoint, self.lexicalEnvironment.lookModule())
    
    def visitAllocaMutableWithValueNode(self, node: ASTAllocaMutableWithValueNode):
        initialValue = self.visitNode(node.initialValue)
        valueType = decayDecorationsOfTypeExpression(getTypeOfAnalyzedNode(initialValue, node.sourcePosition))
        referenceType = self.visitNode(ASTFormReferenceTypeNode(node.sourcePosition, ASTFormDecoratedTypeNode(node.sourcePosition, valueType, DecoratedType.Mutable)))
        return ASTTypedAllocaMutableWithValueNode(node.sourcePosition, referenceType, valueType, initialValue)

    def visitBindableNameNode(self, node: ASTBindableNameNode):
        return self.makeSemanticError(node.sourcePosition, 'Bindable name without assignment or functional context.', node)

    def visitBinaryExpressionSequenceNode(self, node: ASTBinaryExpressionSequenceNode):
        if len(node.elements) == 3:
            return self.visitNode(ASTMessageSendNode(node.sourcePosition, node.elements[0], node.elements[1], [node.elements[2]]))
        assert False

    def visitErrorNode(self, node: ASTErrorNode):
        errorNode = ASTTypedErrorNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbortType), node.message, [])
        self.errorAccumulator.add(errorNode)
        return errorNode

    def visitFunctionNode(self, node: ASTFunctionNode):
        functionalTypeNode: ASTFunctionalDependentTypeNode = self.visitNodeForMacroExpansionOnly(node.functionalType)
        if not functionalTypeNode.isFunctionalDependentTypeNode() and not functionalTypeNode.isTypedErrorNode():
            functionalTypeNode = self.makeSemanticError(functionalTypeNode.sourcePosition, 'Expected a function type expression.', functionalTypeNode)
        if functionalTypeNode.isTypedErrorNode():
           return self.visitNode(ASTSequenceNode(node.sourcePosition, [functionalTypeNode, node.body]))
        
        lambdaNode = functionalTypeNode.constructLambdaWithBody(node.nameExpression, node.body, node.isFixpoint)
        return self.visitNode(lambdaNode)
    
    def visitFunctionTypeNode(self, node: ASTFunctionTypeNode):
        argumentType = self.visitTypeExpression(node.argumentType)
        resultType = self.visitTypeExpression(node.resultType)
        typeUniverse = mergeTypeUniversesOfTypeNodePair(argumentType, resultType, node.sourcePosition)
        return reduceFunctionTypeNode(ASTTypedFunctionTypeNode(node.sourcePosition, typeUniverse, argumentType, resultType))

    def visitFunctionalDependentTypeNode(self, node: ASTFunctionalDependentTypeNode):
        if node.argumentPattern is None:
            return self.visitNode(ASTPiNode(node.sourcePosition, [], False, node.resultType, node.callingConvention))
        
        argumentNodes, isExistential, isVariadic = node.argumentPattern.parseAndUnpackArgumentsPattern()
        if isExistential:
            return self.visitNode(ASTSigmaNode(node.sourcePosition, argumentNodes, node.resultType))
        else:
            return self.visitNode(ASTPiNode(node.sourcePosition, argumentNodes, isVariadic, node.resultType, node.callingConvention))
    
    def analyzeIdentifierReferenceNodeWithBinding(self, node: ASTIdentifierReferenceNode, binding: SymbolBinding) -> ASTNode:
        if binding.isValueBinding():
            if binding.value.isType():
                return ASTLiteralTypeNode(node.sourcePosition, binding.value)
            return ASTTypedLiteralNode(node.sourcePosition, binding.getTypeExpression(), binding.value)
        return ASTTypedIdentifierReferenceNode(node.sourcePosition, binding.getTypeExpression(), binding)
    
    def visitFormDecoratedTypeNode(self, node: ASTFormDecoratedTypeNode):
        baseType = self.visitTypeExpression(node.baseType)
        return reduceDecoratedTypeNode(ASTDecoratedTypeNode(node.sourcePosition, baseType, node.decorations))

    def visitFormPointerTypeNode(self, node: ASTFormPointerTypeNode):
        baseType = self.visitTypeExpression(node.baseType)
        return reducePointerTypeNode(ASTPointerTypeNode(node.sourcePosition, baseType))

    def visitFormReferenceTypeNode(self, node: ASTFormReferenceTypeNode):
        baseType = self.visitTypeExpression(node.baseType)
        return reduceReferenceTypeNode(ASTPointerTypeNode(node.sourcePosition, baseType))

    def visitFormTemporaryReferenceTypeNode(self, node: ASTFormTemporaryReferenceTypeNode):
        baseType = self.visitTypeExpression(node.baseType)
        return reduceTemporaryReferenceTypeNode(ASTPointerTypeNode(node.sourcePosition, baseType))

    def visitFormArrayTypeNode(self, node: ASTFormArrayTypeNode):
        elementType = self.visitTypeExpression(node.elementType)
        size = self.visitNodeWithExpectedType(node.size, SizeType)
        return reduceArrayType(ASTArrayTypeNode(node.sourcePosition, elementType, size))

    def visitFormDictionaryTypeNode(self, node: ASTFormDictionaryTypeNode):
        keyType = self.visitNode(node.keyType)
        valueType = self.visitNode(node.valueType)
        return reduceDictionaryTypeNode(ASTDictionaryTypeNode(node.sourcePosition, keyType, valueType))

    def visitFormInductiveTypeNode(self, node: ASTFormInductiveTypeNode):
        name = self.evaluateOptionalSymbol(node.name)
        if name is None:
            return self.visitNode(node.content)
        
        recursiveBinding = SymbolRecursiveBinding(node.sourcePosition, name, ASTLiteralTypeNode(node.sourcePosition, TypeUniverse.getWithIndex(0)))
        recursiveEnvironment = self.lexicalEnvironment.withSymbolBinding(recursiveBinding)
        analyzedContent = self.withEnvironment(recursiveEnvironment).visitTypeExpression(node.content)
        analyzedContentType = getTypeOfAnalyzedNode(analyzedContent, node.sourcePosition)
        assert analyzedContentType.isLiteralTypeNode() and analyzedContentType.value.isTypeUniverse()

        recursiveBinding.typeExpression = analyzedContentType
        analyzedNode = ASTInductiveTypeNode(node.sourcePosition, name, recursiveBinding, analyzedContent)
        return self.makeBindingForTypeNode(name, analyzedNode)

    def visitFormProductTypeNode(self, node: ASTFormProductTypeNode):
        name = self.evaluateOptionalSymbol(node.name)
        elementTypes = []
        for expression in node.elements:
            elementTypes.append(self.visitTypeExpression(expression))
        return self.makeBindingForTypeNode(name, reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, name, elementTypes)))

    def unpackAssociationNode(self, node: ASTNode):
        if not node.isTupleNode() and not node.isTypedTupleNode():
            return ASTErrorNode(node.sourcePosition, 'Expected a a tuple.'), ASTErrorNode(node.sourcePosition, 'Expected a a tuple.')

        tupleElements = node.elements
        if len(tupleElements) != 2:
            return ASTErrorNode(node.sourcePosition, 'Expected a tuple with two elements.'), ASTErrorNode(node.sourcePosition, 'Expected a tuple with two elements.')
        return tupleElements[0], tupleElements[1]

    def unpackTypeListNode(self, node: ASTNode):
        if not node.isTupleNode() and not node.isTypedTupleNode():
            return [node], None

        return node.elements, None

    def expandAndUnpackDictionaryNodeWithElements(self, node: ASTNode):
        expandedNode = self.visitNodeForMacroExpansionOnly(node)
        if not expandedNode.isDictionaryNode() and not expandedNode.isTypedDictionaryNode():
            return None, ASTErrorNode(node.sourcePosition, 'Expected a dictionary.')
        
        unpackedElements = []
        for element in expandedNode.elements:
            unpackedElements.append(self.unpackAssociationNode(element))

        return unpackedElements, None
    
    def expandAndUnpackUnzippedDictionaryNodeWithElements(self, node: ASTNode):
        keysAndValues, errorNode = self.expandAndUnpackDictionaryNodeWithElements(node)
        if keysAndValues is None:
            return None, None, errorNode

        keys = []
        values = []
        for key, value in keysAndValues:
            keys.append(key)
            values.append(value)
        return keys, values, errorNode
    
    def makeBindingForTypeNode(self, name: Symbol, typeNode: ASTTypeNode):
        if name is None:
            return typeNode
        
        if typeNode.isLiteralTypeNode():
            typeBinding = SymbolValueBinding(typeNode.sourcePosition, name, typeNode.value)
            self.lexicalEnvironment = self.lexicalEnvironment.withSymbolBinding(typeBinding)
            return typeNode

        typeUniverse = ASTLiteralTypeNode(typeNode.sourcePosition, typeNode.getTypeUniverse())
        typeBinding = SymbolLocalBinding(typeNode.sourcePosition, name, typeUniverse, typeNode, False)
        self.lexicalEnvironment = self.lexicalEnvironment.withSymbolBinding(typeBinding)
        return ASTTypedBindingDefinitionNode(typeNode.sourcePosition, typeUniverse, typeBinding, typeNode, isMutable = False, isPublic = False, module = None)
    
    def bindAnonymousValueExpression(self, valueExpression: ASTNode, sourcePosition: SourcePosition):
        typedValue = self.visitNode(valueExpression)
        if typedValue.isTypedLiteralNode() or typedValue.isLiteralTypeNode():
            return [], valueExpression
        
        typeExpression = getTypeOfAnalyzedNode(typedValue, sourcePosition)
        valueBinding = SymbolLocalBinding(sourcePosition, None, typeExpression, typedValue, False)
        bindingDefinitionNode = ASTTypedBindingDefinitionNode(sourcePosition, typeExpression, valueBinding, typedValue, isMutable = False, isPublic = False, module = None)
        bindingReferenceNode = ASTTypedIdentifierReferenceNode(sourcePosition, typeExpression, valueBinding)
        return [bindingDefinitionNode], bindingReferenceNode
        
    def visitFormRecordTypeNode(self, node: ASTFormRecordTypeNode):
        name = self.evaluateOptionalSymbol(node.name)
        assert len(node.fieldNames) == len(node.fieldTypes)
        fieldTypes = []
        fieldNames = []
        for fieldType in node.fieldTypes:
            fieldTypes.append(self.visitTypeExpression(fieldType))
        for fieldName in node.fieldNames:
            fieldNames.append(self.evaluateOptionalSymbol(fieldName))

        return self.makeBindingForTypeNode(name, reduceRecordTypeNode(ASTRecordTypeNode(node.sourcePosition, name, fieldTypes, fieldNames, node.isRecursive)))

    def visitFormSumTypeNode(self, node: ASTFormSumTypeNode):
        elementTypes = []
        for expression in node.elements:
            elementTypes.append(self.visitTypeExpression(expression))
        return reduceSumTypeNode(ASTSumTypeNode(node.sourcePosition, elementTypes))

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
    
    def visitIfNode(self, node: ASTIfNode):
        condition = self.visitNodeWithExpectedType(node.condition, BooleanType)
        trueExpression = node.trueExpression
        if trueExpression is None:
            trueExpression = ASTLiteralNode(node.sourcePosition, VoidType.getSingleton())
        trueExpression = self.visitNodeWithCurrentExpectedType(trueExpression)

        falseExpression = node.falseExpression
        if falseExpression is None:
            falseExpression = ASTLiteralNode(node.sourcePosition, VoidType.getSingleton())
        falseExpression = self.visitNodeWithCurrentExpectedType(falseExpression)

        type = self.mergeTypesOfBranch(getTypeOfAnalyzedNode(trueExpression, trueExpression.sourcePosition), getTypeOfAnalyzedNode(falseExpression, falseExpression.sourcePosition), node.sourcePosition)
        ifNode = ASTTypedIfNode(node.sourcePosition, type, condition, trueExpression, falseExpression)
        return reduceIfNode(ifNode)
    
    def visitBreakNode(self, node: ASTBreakNode):
        if not self.lexicalEnvironment.isValidContextForBreak():
            return self.makeSemanticError(node.sourcePosition, 'Invalid location for a break expression.', node)
        return ASTTypedBreakNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbortType))

    def visitContinueNode(self, node: ASTBreakNode):
        if not self.lexicalEnvironment.isValidContextForContinue():
            return self.makeSemanticError(node.sourcePosition, 'Invalid location for a continue expression.', node)
        return ASTTypedContinueNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbortType))

    def visitDoWhileNode(self, node: ASTWhileNode):
        bodyExpression = node.bodyExpression
        if bodyExpression is None:
            bodyExpression = ASTLiteralNode(node.sourcePosition, VoidType.getSingleton())
        
        loopEnvironment = LexicalEnvironment(ChildEnvironmentBreakAndContinue(self.lexicalEnvironment), node.sourcePosition)
        bodyExpression = self.withEnvironment(loopEnvironment).visitNode(bodyExpression)

        condition = node.condition
        if condition is None:
            self.condition = ASTLiteralNode(node.sourcePosition, TrueValue.getSingleton())
        condition = self.visitNodeWithExpectedType(condition, BooleanType)

        continueExpression = node.continueExpression
        if continueExpression is None:
            continueExpression = ASTLiteralNode(node.sourcePosition, VoidType.getSingleton())
        continueExpression = self.visitNode(continueExpression)

        type = ASTLiteralTypeNode(node.sourcePosition, VoidType)
        doWhileNode = ASTTypedDoWhileNode(node.sourcePosition, type, bodyExpression, condition, continueExpression)
        return reduceDoWhileNode(doWhileNode)
    
    def visitWhileNode(self, node: ASTWhileNode):
        condition = node.condition
        if condition is None:
            self.condition = ASTLiteralNode(node.sourcePosition, TrueValue.getSingleton())
        condition = self.visitNodeWithExpectedType(condition, BooleanType)

        bodyExpression = node.bodyExpression
        if bodyExpression is None:
            bodyExpression = ASTLiteralNode(node.sourcePosition, VoidType.getSingleton())
        
        loopEnvironment = LexicalEnvironment(ChildEnvironmentBreakAndContinue(self.lexicalEnvironment), node.sourcePosition)
        bodyExpression = self.withEnvironment(loopEnvironment).visitNode(bodyExpression)

        continueExpression = node.continueExpression
        if continueExpression is None:
            continueExpression = ASTLiteralNode(node.sourcePosition, VoidType.getSingleton())
        continueExpression = self.visitNode(continueExpression)

        type = ASTLiteralTypeNode(node.sourcePosition, VoidType)
        whileNode = ASTTypedWhileNode(node.sourcePosition, type, condition, bodyExpression, continueExpression)
        return reduceWhileNode(whileNode)

    def analyzeArgumentNode(self, node: ASTBindableNameNode) -> ASTTypedArgumentNode:
        assert node.isBindableNameNode()
        name = self.evaluateOptionalSymbol(node.nameExpression)
        type = self.visitOptionalTypeExpression(node.typeExpression)
        if type is None:
            type = ASTLiteralTypeNode(node.sourcePosition, AnyType)
        binding = SymbolArgumentBinding(node.sourcePosition, name, type, isImplicit = node.isImplicit)
        return ASTTypedArgumentNode(node.sourcePosition, type, binding, node.isImplicit, node.isExistential)

    def visitLambdaNode(self, node: ASTLambdaNode):
        functionalEnvironment = FunctionalAnalysisEnvironment(self.lexicalEnvironment, [], node.sourcePosition)
        typedArguments = []
        for argument in node.arguments:
            typedArgument = self.withEnvironment(functionalEnvironment).analyzeArgumentNode(argument)
            functionalEnvironment = functionalEnvironment.withArgumentBinding(typedArgument.binding)
            typedArguments.append(typedArgument)

        # Analyze here the result type expression, so that we can introduce the fixpoint binding without poluting the environment
        analyzedResultTypeExpression = None
        if node.resultType is not None:
            analyzedResultTypeExpression = self.withEnvironment(functionalEnvironment).visitTypeExpression(node.resultType)

        name = self.evaluateOptionalSymbol(node.nameExpression)

        # Construct the dependent type without result type inference.
        typedPi = None
        if (analyzedResultTypeExpression is not None) or (node.isFixpoint and name is not None):
            typeUniverse = mergeTypeUniversesOfTypeNodes([getTypeOfAnalyzedNode(analyzedResultTypeExpression, node.sourcePosition)] + list(map(lambda a: getTypeOfAnalyzedNode(a, node.sourcePosition), typedArguments)), node.sourcePosition)
            typedPi = reducePiNode(ASTTypedPiNode(node.sourcePosition, None, typeUniverse, typedArguments, node.isVariadic, functionalEnvironment.captureBindings, analyzedResultTypeExpression, node.callingConvention))

        # Add the fixpoint symbol.
        fixpointBinding = None
        if node.isFixpoint and name is not None:
            fixpointBinding = SymbolFixpointBinding(node.sourcePosition, name, typedPi)
            functionalEnvironment = functionalEnvironment.withFixpointBinding(fixpointBinding)

        # Analyze the body
        body = self.withEnvironment(functionalEnvironment).visitNodeWithExpectedTypeExpression(node.body, analyzedResultTypeExpression)

        # Compute the lambda type.
        bodyType = getTypeOfAnalyzedNode(body, node.sourcePosition)
        typeUniverse = mergeTypeUniversesOfTypeNodes([body] + list(map(lambda a: getTypeOfAnalyzedNode(a, node.sourcePosition), typedArguments)), node.sourcePosition)
        if typedPi is None:
            typedPi = reducePiNode(ASTTypedPiNode(node.sourcePosition, None, typeUniverse, typedArguments, node.isVariadic, functionalEnvironment.captureBindings, bodyType, node.callingConvention))

        # Make the lambda node.
        return reduceLambdaNode(ASTTypedLambdaNode(node.sourcePosition, name, typedPi, typedArguments, node.isVariadic, functionalEnvironment.captureBindings, fixpointBinding, body, node.callingConvention))

    def visitPiNode(self, node: ASTPiNode):
        functionalEnvironment = FunctionalAnalysisEnvironment(self.lexicalEnvironment, [], node.sourcePosition)
        typedArguments = []
        for argument in node.arguments:
            typedArgument = self.withEnvironment(functionalEnvironment).analyzeArgumentNode(argument)
            functionalEnvironment = functionalEnvironment.withArgumentBinding(typedArgument.binding)
            typedArguments.append(typedArgument)

        if node.body is None:
            body = ASTLiteralTypeNode(node.sourcePosition, AnyType)
        else:
            body = self.withEnvironment(functionalEnvironment).visitTypeExpression(node.body)
        typeUniverse = mergeTypeUniversesOfTypeNodes([body] + list(map(lambda a: getTypeOfAnalyzedNode(a, node.sourcePosition), typedArguments)), node.sourcePosition)
        return reducePiNode(ASTTypedPiNode(node.sourcePosition, None, typeUniverse, typedArguments, node.isVariadic, functionalEnvironment.captureBindings, body, node.callingConvention))

    def visitSigmaNode(self, node: ASTSigmaNode):
        functionalEnvironment = FunctionalAnalysisEnvironment(self.lexicalEnvironment, [], node.sourcePosition)
        typedArguments = []
        for argument in node.arguments:
            typedArgument = self.withEnvironment(functionalEnvironment).analyzeArgumentNode(argument)
            functionalEnvironment = functionalEnvironment.withArgumentBinding(typedArgument.binding)
            typedArguments.append(typedArgument)

        body = self.withEnvironment(functionalEnvironment).visitTypeExpression(node.body)
        typeUniverse = mergeTypeUniversesOfTypeNodes([body] + list(map(lambda a: getTypeOfAnalyzedNode(a, node.sourcePosition), typedArguments)), node.sourcePosition)
        typedSigma = ASTTypedSigmaNode(node.sourcePosition, None, typeUniverse, typedArguments, False, functionalEnvironment.captureBindings, body, node.callingConvention)
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
        if not node.isMutable and (typecheckedValue.isTypedLiteralNode() or typecheckedValue.isLiteralTypeNode()):
            valueBinding = SymbolValueBinding(node.sourcePosition, localName, typecheckedValue.value)
            if node.isPublic:
                module.exportBinding(valueBinding)
            self.lexicalEnvironment = self.lexicalEnvironment.withSymbolBinding(valueBinding)
            return typecheckedValue

        ## Allocate the box for the mutable value.
        if node.isMutable:
            typecheckedValue = self.visitNode(ASTAllocaMutableWithValueNode(node.sourcePosition, typecheckedValue))

        ## Make a local variable.
        bindingTypeExpression = typecheckedValue.getTypeExpressionAt(node.sourcePosition)

        localBinding = SymbolLocalBinding(node.sourcePosition, localName, bindingTypeExpression, typecheckedValue, node.isMutable)
        if node.isPublic:
            module.exportBinding(localBinding)
        self.lexicalEnvironment = self.lexicalEnvironment.withSymbolBinding(localBinding)
        return ASTTypedBindingDefinitionNode(node.sourcePosition, bindingTypeExpression, localBinding, typecheckedValue, isMutable = node.isMutable, isPublic = node.isPublic, module = module)
    
    def visitAssignmentNode(self, node: ASTAssignmentNode):
        expandedStore = self.visitNodeForMacroExpansionOnly(node.store)
        if expandedStore.isFunctionalDependentTypeNode():
            return self.visitNode(ASTFunctionNode(node.sourcePosition, None, expandedStore, node.value, False))
        elif expandedStore.isBindableNameNode():
            bindableName: ASTBindableNameNode = expandedStore
            if bindableName.typeExpression is not None and bindableName.typeExpression.isFunctionalDependentTypeNode():
                functionExpression = ASTFunctionNode(node.sourcePosition, bindableName.nameExpression, bindableName.typeExpression, node.value, bindableName.hasPostTypeExpression)
                return self.visitNode(ASTBindingDefinitionNode(node.sourcePosition, bindableName.nameExpression, None, functionExpression, isRebind = True, isMutable = bindableName.isMutable))
            else:
                return self.visitNode(ASTBindPatternNode(node.sourcePosition, expandedStore, node.value, False))
        
        selector = ASTLiteralNode(node.sourcePosition, Symbol.intern(':='))
        return self.visitNode(ASTMessageSendNode(node.sourcePosition, expandedStore, selector, [node.value]))
    
    def visitBindPatternNode(self, node: ASTBindPatternNode):
        value = self.visitNode(node.value)
        expandedNode = node.pattern.expandBindingOfValueWithAt(value, self, node.sourcePosition)
        return self.visitNode(expandedNode)

    def packMessageSendArguments(self, sourcePosition: SourcePosition, arguments: list[ASTNode]):
        if len(arguments) <= 1:
            return arguments
        return [ASTTupleNode(sourcePosition, arguments)]
    
    def expandMessageSendWithMacro(self, node: ASTMessageSendNode, receiver: ASTNode, macro):
        arguments = [MacroContext(node.sourcePosition, self.lexicalEnvironment, self), receiver] + node.arguments
        return self.visitNode(macro(*arguments))

    def visitMessageSendNode(self, node: ASTMessageSendNode):
        analyzedReceiver = None
        if node.receiver is not None:
            analyzedReceiver = self.visitNode(node.receiver)

        selector, errorNode = self.evaluateSymbol(node.selector)
        if selector is not None:
            if analyzedReceiver.isTypeNode():
                if selector in TypeMacros:
                    return self.expandMessageSendWithMacro(node, analyzedReceiver, TypeMacros[selector])
                
            if analyzedReceiver is not None and not analyzedReceiver.isLiteralTypeNode():
                analyzedReceiverType = getTypeOfAnalyzedNode(analyzedReceiver, node.sourcePosition)
                if analyzedReceiverType.isReferenceLikeTypeNodeOrLiteral():
                    if selector in ReferenceLikeTypeMacros:
                        return self.expandMessageSendWithMacro(node, analyzedReceiver, ReferenceLikeTypeMacros[selector])

                if analyzedReceiverType.isArrayTypeNodeOrLiteral():
                    if selector in ArrayTypeMacros:
                        return self.expandMessageSendWithMacro(node, analyzedReceiver, ArrayTypeMacros[selector])
                if analyzedReceiverType.isPointerTypeNodeOrLiteral():
                    if selector in PointerTypeMacros:
                        return self.expandMessageSendWithMacro(node, analyzedReceiver, PointerTypeMacros[selector])

                ## Getter.
                analyzedDecayedReceiverType = decayTypeExpression(analyzedReceiverType)
                if len(node.arguments) == 0:
                    fieldIndex, fieldType = analyzedDecayedReceiverType.findIndexOfFieldOrNoneAt(selector, node.sourcePosition)
                    if fieldIndex is not None:
                        return self.visitNode(ASTTupleAtNode(node.sourcePosition, analyzedReceiver, ASTLiteralNode(node.sourcePosition, IntegerValue(fieldIndex))))

            selectorNode = ASTIdentifierReferenceNode(node.selector.sourcePosition, selector)
        else:
            selectorNode = errorNode
        
        if analyzedReceiver is None:
            return self.visitNode(ASTApplicationNode(node.sourcePosition, selectorNode, self.packMessageSendArguments(node.sourcePosition, node.arguments)))
        else:
            return self.visitNode(ASTApplicationNode(node.sourcePosition, selectorNode, self.packMessageSendArguments(node.sourcePosition, [analyzedReceiver] + node.arguments)))
        
    def extraAssociationKeyAndValueType(self, node: ASTTypedNode):
        typeNode = getTypeOfAnalyzedNode(node, node.sourcePosition)
        if not typeNode.isProductTypeNodeOrLiteral():
            anyTypeLiteral = ASTLiteralTypeNode(node.sourcePosition, AnyType)
            return self.makeSemanticError(node.sourcePosition, 'Expected an association, which is tuple with two elements.'), anyTypeLiteral, anyTypeLiteral
        
        if typeNode.isLiteralTypeNode():
            if len(typeNode.value.elementTypes) != 2:
                anyTypeLiteral = ASTLiteralTypeNode(node.sourcePosition, AnyType)
                return self.makeSemanticError(node.sourcePosition, 'Expected an association, which is tuple with two elements.'), anyTypeLiteral, anyTypeLiteral
            keyType = ASTLiteralTypeNode(node.sourcePosition, typeNode.value.elementTypes[0])
            valueType = ASTLiteralTypeNode(node.sourcePosition, typeNode.value.elementTypes[1])
            return node, keyType, valueType
        else:
            if len(typeNode.elements) != 2:
                anyTypeLiteral = ASTLiteralTypeNode(node.sourcePosition, AnyType)
                return self.makeSemanticError(node.sourcePosition, 'Expected an association, which is tuple with two elements.'), anyTypeLiteral, anyTypeLiteral
            return node, typeNode.elements[0], typeNode.elements[1]

    def visitDictionaryNode(self, node: ASTDictionaryNode):
        elements = []
        keyTypes = []
        valueTypes = []
        for element in node.elements:
            typedElement, keyType, valueType = self.extraAssociationKeyAndValueType(self.visitNode(element))
            elements.append(typedElement)
            keyTypes.append(keyType)
            valueTypes.append(valueType)

        anyTypeLiteral = ASTLiteralTypeNode(node.sourcePosition, AnyType)
        keyType = self.mergeListOfTypes(keyTypes, anyTypeLiteral, node.sourcePosition)
        valueType = self.mergeListOfTypes(valueTypes, anyTypeLiteral, node.sourcePosition)
        dictionaryType = self.visitNode(ASTFormDictionaryTypeNode(node.sourcePosition, keyType, valueType))
        associationType = self.visitNode(ASTFormProductTypeNode(node.sourcePosition, None, [keyType, valueType]))

        coercedElements = []
        for element in elements:
            coercedElements.append(self.visitNodeWithExpectedTypeExpression(element, associationType))

        return reduceDictionaryNode(ASTTypedDictionaryNode(node.sourcePosition, dictionaryType, coercedElements))

    def visitSequenceNode(self, node: ASTSequenceNode):
        if len(node.elements) == 0:
            return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, VoidType), VoidType.getSingleton())
        elif len(node.elements) == 1:
            return self.visitNode(node.elements[0])
        
        resultType = VoidType
        typedElements = []
        expressionCount = len(node.elements)
        for i in range(expressionCount):
            expression = node.elements[i]
            typedExpression = self.visitNode(expression)
            if i + 1 < expressionCount and (typedExpression.isTypedLiteralNode() or typedExpression.isLiteralTypeNode()):
                continue

            resultType = getTypeOfAnalyzedNode(typedExpression, node.sourcePosition)
            typedElements.append(typedExpression)

        if len(typedElements) == 1:
            return typedElements[0]
        return ASTTypedSequenceNode(node.sourcePosition, resultType, typedElements)

    def visitArraySubscriptAtNode(self, node: ASTArraySubscriptAtNode):
        array = self.visitNode(node.array)
        index = self.visitNodeWithExpectedType(node.index, SizeType)
        arrayType = decayTypeExpression(getTypeOfAnalyzedNode(array, node.sourcePosition))
        elementType = arrayType.getElementTypeExpressionAt(node.sourcePosition)
        if node.resultAsReference:
            resultType = self.visitNode(ASTFormReferenceTypeNode(node.sourcePosition, elementType))
        elif node.resultAsPointer:
            resultType = self.visitNode(ASTFormPointerTypeNode(node.sourcePosition, elementType))
        else:
            resultType = decayTypeExpression(elementType)
        return reduceArraySubscriptAtNode(ASTTypedArraySubscriptAtNode(node.sourcePosition, resultType, array, index, not (node.resultAsReference or node.resultAsPointer)))

    def visitPointerLikeLoadNode(self, node: ASTPointerLikeLoadNode):
        pointer = self.visitNode(node.pointer)
        pointerType = getTypeOfAnalyzedNode(pointer, node.sourcePosition)
        baseType = pointerType.getBaseTypeExpressionAt(node.sourcePosition)
        isVolatile = isVolatileDecoratedTypeExpression(baseType)
        baseType = decayDecorationsOfTypeExpression(baseType)
        return ASTTypedPointerLikeLoadNode(node.sourcePosition, baseType, pointer, isVolatile = isVolatile)

    def visitPointerLikeStoreNode(self, node: ASTPointerLikeStoreNode):
        pointer = self.visitNode(node.pointer)
        pointerType = getTypeOfAnalyzedNode(pointer, node.sourcePosition)
        baseType = pointerType.getBaseTypeExpressionAt(node.sourcePosition)
        isVolatile = isVolatileDecoratedTypeExpression(baseType)
        if not isMutableDecoratedTypeExpression(baseType):
            pointer = self.makeSemanticError(node.sourcePosition, 'Cannot perform store into non-mutable pointer or reference.', baseType)

        baseType = decayDecorationsOfTypeExpression(baseType)
        value = self.visitNodeWithExpectedTypeExpression(node.value, baseType)
        resultType = value
        if node.returnPointer:
            resultType = pointerType
        return ASTTypedPointerLikeStoreNode(node.sourcePosition, resultType, pointer, value, node.returnPointer, isVolatile = isVolatile)

    def visitPointerLikeReinterpretToNode(self, node: ASTPointerLikeReinterpretToNode):
        pointer = self.visitNode(node.pointer)
        targetType = self.visitTypeExpression(node.targetType)
        return reducePointerLikeReinterpretToNode(ASTTypedPointerLikeReinterpretToNode(node.sourcePosition, targetType, pointer))

    def visitPointerLikeSubscriptAtNode(self, node: ASTPointerLikeSubscriptAtNode):
        pointer = self.visitNode(node.pointer)
        index = self.visitNodeWithExpectedTypeAlternative(node.index, [SizeType, UIntPointerType, IntPointerType])
        pointerType = getTypeOfAnalyzedNode(pointer, node.sourcePosition)
        resultType = pointerType
        if node.resultAsReference:
            baseType = pointerType.getBaseTypeExpressionAt(node.sourcePosition)
            resultType = self.vistNode(ASTFormReferenceTypeNode(node.sourcePosition, baseType))
        return ASTTypedPointerLikeSubscriptAtNode(node.sourcePosition, resultType, pointer, index)

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
            return ASTTypedLiteralNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, VoidType), VoidType.getSingleton())
        elif len(node.elements) == 1:
            return self.visitNode(node.elements[0])
        
        elementTypeExpressions = []
        typedElements = []
        for expression in node.elements:
            typedExpression = self.visitNode(expression)
            elementTypeExpressions.append(getTypeOfAnalyzedNode(typedExpression, typedExpression.sourcePosition))
            typedElements.append(typedExpression)

        if all(isLiteralTypeOfTypeNode(elementType) for elementType in elementTypeExpressions):
            return reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, None, typedElements))
        
        tupleType = reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, None, elementTypeExpressions))
        return reduceTupleNode(ASTTypedTupleNode(node.sourcePosition, tupleType, typedElements, False))

    def visitTupleAtNode(self, node: ASTTupleAtNode):
        tuple = self.visitNode(node.tuple)
        indexValue, indexValueError = self.evaluateInteger(node.index)
        if indexValueError is not None:
            return self.visitNode(ASTSequenceNode(node.sourcePosition, [tuple, indexValueError]))
        index: int = indexValue.value

        tupleType = getTypeOfAnalyzedNode(tuple, node.sourcePosition)
        tupleDecayedType = decayTypeExpression(tupleType)
        tupleIsReferenceLike = tupleType.isReferenceLikeTypeNodeOrLiteral()
        tupleElementType = tupleDecayedType.findTypeOfFieldAtIndexOrNoneAt(index, node.sourcePosition)
        if tupleElementType is None:
            return self.visitNode(ASTSequenceNode(node.sourcePosition, [tuple, ASTErrorNode(node.sourcePosition, '%s does not have a field at index %d.' % (tupleType.prettyPrint(), index))]))

        if tupleIsReferenceLike:
            fieldResultType = self.visitNode(ASTFormReferenceTypeNode(node.sourcePosition, tupleElementType))
        else:
            fieldResultType = tupleElementType
        return reduceTupleAtNode(ASTTypedTupleAtNode(node.sourcePosition, fieldResultType, tuple, index, not tupleIsReferenceLike))

    def visitRecordNode(self, node: ASTRecordNode):
        recordTypeExpression = self.visitTypeExpression(node.type)
        if not recordTypeExpression.isRecordTypeNodeOrLiteral():
            return self.visitNode(ASTSequenceNode(node.sourcePosition,
                node.fieldNames + node.fieldValues + [ASTErrorNode(recordTypeExpression.sourcePosition, "Expected a record type.")])
            )
        
        errorNodes = []
        coercedFieldValues = []
        fieldValues = [None] * len(recordTypeExpression.value.elementTypes)
        for i in range(len(node.fieldNames)):
            fieldNameExpression = node.fieldNames[i]
            fieldName, errorNode = self.evaluateSymbol(fieldNameExpression)
            if errorNode is not None:
                errorNodes.append(errorNode)
                continue

            fieldIndex, fieldType = recordTypeExpression.findIndexOfFieldOrNoneAt(fieldName, fieldNameExpression.sourcePosition)
            if fieldIndex is None:
                errorNodes.append(ASTErrorNode(fieldName.sourcePosition, 'Failed to find field %s in record %s.' % (fieldName.prettyPrint(), recordTypeExpression.prettyPrint())))
                continue

            fieldValue = self.visitNodeWithExpectedTypeExpression(node.fieldValues[i], fieldType)
            coercedFieldValues.append(fieldValue)
            if fieldValues[i] is not None:
                errorNodes.append(fieldValue)
                errorNodes.append(ASTErrorNode(fieldName.sourcePosition, 'Field %s initialization is duplication.' % fieldName.prettyPrint()))
                
                continue

            fieldValues[i] = fieldValue

        ## Make sure all of the fields are set.
        for i in range(len(fieldValues)):
            if fieldValues[i] is None:
                assert False

        if len(errorNodes):
            return self.visitNode(ASTSequenceNode(node.sourcePosition, coercedFieldValues + errorNodes))
        
        return reduceTupleNode(ASTTypedTupleNode(node.sourcePosition, recordTypeExpression, fieldValues, True))

    def visitModifiedRecordNode(self, node: ASTModifiedRecordNode):
        record = self.visitNode(node.record)
        recordTypeExpression = getTypeOfAnalyzedNode(record, node.sourcePosition)
        if not recordTypeExpression.isRecordTypeNodeOrLiteral():
            return self.visitNode(ASTSequenceNode(node.sourcePosition,
                [record] + node.fieldNames + node.fieldValues + [ASTErrorNode(recordTypeExpression.sourcePosition, "Expected a record type.")])
            )
        
        errorNodes = []
        coercedFieldValues = []
        elementIndices = []
        for i in range(len(node.fieldNames)):
            fieldNameExpression = node.fieldNames[i]
            fieldName, errorNode = self.evaluateSymbol(fieldNameExpression)
            if errorNode is not None:
                errorNodes.append(errorNode)
                continue

            fieldIndex, fieldType = recordTypeExpression.findIndexOfFieldOrNoneAt(fieldName, fieldNameExpression.sourcePosition)
            if fieldIndex is None:
                errorNodes.append(ASTErrorNode(fieldNameExpression.sourcePosition, 'Failed to find field %s in record %s.' % (fieldName.prettyPrint(), recordTypeExpression.prettyPrint())))
                continue

            fieldValue = self.visitNodeWithExpectedTypeExpression(node.fieldValues[i], fieldType)
            elementIndices.append(fieldIndex)
            coercedFieldValues.append(fieldValue)

        if len(errorNodes):
            return self.visitNode(ASTSequenceNode(node.sourcePosition, coercedFieldValues + errorNodes))
        
        return reduceModifiedTupleNode(ASTTypedModifiedTupleNode(node.sourcePosition, recordTypeExpression, record, coercedFieldValues, elementIndices, True))
    
    def visitOverloadsTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitDecoratedTypeNode(self, node: ASTDecoratedTypeNode):
        return node

    def visitPointerTypeNode(self, node: ASTPointerTypeNode):
        return node

    def visitReferenceTypeNode(self, node: ASTReferenceTypeNode):
        return node

    def visitTemporaryReferenceTypeNode(self, node: ASTTemporaryReferenceTypeNode):
        return node

    def visitArrayTypeNode(self, node: ASTArrayTypeNode):
        return node

    def visitInductiveTypeNode(self, node: ASTInductiveTypeNode):
        return node

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitRecordTypeNode(self, node: ASTRecordTypeNode):
        return node

    def visitSumTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitDictionaryTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitTypedAllocaMutableWithValueNode(self, node: ASTTypedAllocaMutableWithValueNode):
        return node

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        return node

    def visitTypedArgumentNode(self, node: ASTTypedArgumentNode):
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

    def visitTypedIfNode(self, node: ASTTypedIfNode):
        return node

    def visitTypedBreakNode(self, node: ASTTypedBreakNode):
        return node

    def visitTypedContinueNode(self, node: ASTTypedContinueNode):
        return node

    def visitTypedDoWhileNode(self, node: ASTTypedDoWhileNode):
        return node

    def visitTypedWhileNode(self, node: ASTTypedWhileNode):
        return node

    def visitTypedImplicitValueNode(self, node):
        return node

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        return node

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        return node

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode):
        return node

    def visitTypedOverloadedApplicationNode(self, node: ASTTypedOverloadedApplicationNode):
        return node

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode):
        return node

    def visitTypedArraySubscriptAtNode(self, node: ASTTypedArraySubscriptAtNode):
        return node

    def visitTypedPointerLikeLoadNode(self, node: ASTTypedPointerLikeLoadNode):
        return node

    def visitTypedPointerLikeStoreNode(self, node: ASTTypedPointerLikeStoreNode):
        return node

    def visitTypedPointerLikeReinterpretToNode(self, node: ASTTypedPointerLikeReinterpretToNode):
        return node

    def visitTypedPointerLikeSubscriptAtNode(self, node: ASTTypedPointerLikeSubscriptAtNode):
        return node

    def visitTypedDictionaryNode(self, node: ASTTypedDictionaryNode):
        return node

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode):
        return node

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        return node

    def visitTypedModifiedTupleNode(self, node: ASTTypedModifiedTupleNode):
        return node

    def visitTypedTupleAtNode(self, node: ASTTypedTupleAtNode):
        return node

    def visitTypedInjectSumNode(self, node: ASTTypedTupleNode):
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

    def lookSubstitutionForBindingInNode(self, binding: SymbolBinding, oldNode: ASTTypedNode) -> ASTNode:
        if binding in self.bindingSubstitutionNodes:
            return self.applySourcePositionToSubstitution(self.bindingSubstitutionNodes[binding], oldNode.sourcePosition)
        if binding in self.bindingSubstitutionBindings:
            assert oldNode.isTypedIdentifierReferenceNode()
            newBinding = self.bindingSubstitutionBindings[binding]
            return ASTTypedIdentifierReferenceNode(oldNode.sourcePosition, newBinding.getTypeExpression(), newBinding)

        if self.parent is not None:
            return self.parent.lookSubstitutionForBindingInNode(binding, oldNode)
        return oldNode

    def lookSubstitutionForCapturedBindingInNode(self, binding: SymbolBinding):
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

    def setSubstitutionNodeForBinding(self, binding: SymbolBinding, substitution: ASTNode) -> None:
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
        for argument in node.arguments:
            self.visitNode(argument.type)
        for captureBinding in node.captureBindings:
            self.context.getOrCreateCaptureForBinding(captureBinding.capturedBinding)

    def visitTypedPiNode(self, node: ASTTypedPiNode):
        self.visitNode(node.type)
        for argument in node.arguments:
            self.visitNode(argument.type)
        for captureBinding in node.captureBindings:
            self.context.getOrCreateCaptureForBinding(captureBinding.capturedBinding)
    
class ASTBetaReducer(ASTTypecheckedVisitor):
    def __init__(self, substitutionContext: SubstitutionContext) -> None:
        super().__init__()
        self.substitutionContext = substitutionContext

    def visitNode(self, node: ASTNode) -> ASTNode:
        return node.accept(self)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode) -> ASTLiteralTypeNode:
        return node
    
    def visitTypedAllocaMutableWithValueNode(self, node: ASTTypedAllocaMutableWithValueNode):
        type = self.visitNode(node.type)
        valueType = self.visitNode(node.valueType)
        initialValue = self.visitNode(node.initialValue)
        return ASTTypedAllocaMutableWithValueNode(node.sourcePosition, type, valueType, initialValue)
    
    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        for binding, substitution in node.implicitValueSubstitutions:
            self.substitutionContext.setSubstitutionNodeForBinding(binding, self.visitNode(substitution))

        return reduceTypedApplicationNode(ASTTypedApplicationNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.functional), self.visitNode(node.argument), []))

    def visitTypedArgumentNode(self, node: ASTTypedArgumentNode):
        return ASTTypedArgumentNode(node.sourcePosition, self.visitNode(node.type), node.binding, node.isImplicit, node.isExistential)

    def visitTypedErrorNode(self, node: ASTTypedErrorNode):
        return node

    def visitTypedFunctionTypeNode(self, node: ASTTypedFunctionTypeNode):
        newType = self.visitNode(node.type)
        argumentType = self.visitNode(node.argumentType)
        resultType = self.visitNode(node.resultType)
        return reduceFunctionTypeNode(ASTTypedFunctionTypeNode(node.sourcePosition, newType, argumentType, resultType))
    
    def reduceArguments(self, arguments: list[ASTTypedArgumentNode], captureBindings: list[SymbolCaptureBinding]):
        newArguments = []

        bodyContext = SubstitutionContext(self.substitutionContext)
        bodyContext.addSubstitutionsForCaptureBindings(captureBindings)
        reducer = ASTBetaReducer(bodyContext)

        for argument in arguments:
            argumentBinding = argument.binding
            newArgumentType = reducer.visitNode(argumentBinding.typeExpression)
            newArgumentBinding = SymbolArgumentBinding(argumentBinding.sourcePosition, argumentBinding.name, newArgumentType)
            newArgument = ASTTypedArgumentNode(argument.sourcePosition, newArgumentType, newArgumentBinding, isImplicit = argument.isImplicit, isExistential = argument.isExistential)
            newArguments.append(newArgument)

            bodyContext.setSubstitutionBindingForBinding(argumentBinding, newArgumentBinding)

        newCaptureBindings = bodyContext.captureBindings
        return reducer, newArguments, newCaptureBindings

    def visitTypedPiNode(self, node: ASTTypedPiNode):
        newType = self.visitNode(node.type)
        reducer, newArguments, newCaptureBindings = self.reduceArguments(node.arguments, node.captureBindings)

        reducedBody = reducer.visitNode(node.body)
        return reducePiNode(ASTTypedPiNode(node.sourcePosition, node.name, newType, newArguments, newCaptureBindings, reducedBody, node.callingConvention))

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode):
        return node.binding.evaluateSubstitutionInContextFor(self.substitutionContext, node)

    def visitTypedIfNode(self, node: ASTTypedIfNode):
        type = self.visitNode(node.type)
        condition = self.visitNode(node.condition)
        trueExpression = self.visitNode(node.trueExpression)
        falseExpression = self.visitNode(node.falseExpression)
        return reduceIfNode(ASTTypedIfNode(node.sourcePosition, type, condition, trueExpression, falseExpression))
    
    def visitTypedBreakNode(self, node: ASTTypedBreakNode):
        return node

    def visitTypedContinueNode(self, node: ASTTypedContinueNode):
        return node

    def visitTypedDoWhileNode(self, node: ASTTypedDoWhileNode):
        type = self.visitNode(node.type)
        bodyExpression = self.visitNode(node.bodyExpression)
        condition = self.visitNode(node.condition)
        continueExpression = self.visitNode(node.continueExpression)
        return reduceDoWhileNode(ASTTypedDoWhileNode(node.sourcePosition, type, bodyExpression, condition, continueExpression))

    def visitTypedWhileNode(self, node: ASTTypedWhileNode):
        type = self.visitNode(node.type)
        condition = self.visitNode(node.condition)
        bodyExpression = self.visitNode(node.bodyExpression)
        continueExpression = self.visitNode(node.continueExpression)
        return reduceWhileNode(ASTTypedWhileNode(node.sourcePosition, type, condition, bodyExpression, continueExpression))

    def visitTypedImplicitValueNode(self, node):
        return node
    
    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        newType = self.visitNode(node.type)
        reducer, newArguments, newCaptureBindings = self.reduceArguments(node.arguments, node.captureBindings)
        newFixpointBinding = None
        if node.fixpointBinding is not None:
            newFixpointBinding = SymbolFixpointBinding(node.fixpointBinding.sourcePosition, node.fixpointBinding.name, self.visitNode(node.fixpointBinding.typeExpression))
            reducer.substitutionContext.setSubstitutionBindingForBinding(node.fixpointBinding, newFixpointBinding)

        reducedBody = reducer.visitNode(node.body)
        return reduceLambdaNode(ASTTypedLambdaNode(node.sourcePosition, node.name, newType, newArguments, newCaptureBindings, newFixpointBinding, reducedBody, node.callingConvention))

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode):
        newType = self.visitNode(node.type)
        reducer, newArguments, newCaptureBindings = self.reduceArguments(node.arguments, node.captureBindings)

        reducedBody = reducer.visitNode(node.body)
        return reduceSigmaNode(ASTTypedSigmaNode(node.sourcePosition, node.name, newType, newArguments, newCaptureBindings, reducedBody, node.callingConvention))

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        return node

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode):
        assert False

    def visitTypedArraySubscriptAtNode(self, node: ASTTypedArraySubscriptAtNode):
        type = self.visitNode(node.type)
        array = self.visitNode(node.array)
        index = self.visitNode(node.index)
        return ASTTypedArraySubscriptAtNode(node.sourcePosition, type, array, index, node.loadResult)

    def visitTypedPointerLikeLoadNode(self, node: ASTTypedPointerLikeLoadNode):
        type = self.visitNode(node.type)
        pointer = self.visitNode(node.pointer)
        return ASTTypedPointerLikeLoadNode(node.sourcePosition, type, pointer, isVolatile = node.isVolatile)

    def visitTypedPointerLikeStoreNode(self, node: ASTTypedPointerLikeStoreNode):
        type = self.visitNode(node.type)
        pointer = self.visitNode(node.pointer)
        value = self.visitNode(node.value)
        return ASTTypedPointerLikeStoreNode(node.sourcePosition, type, pointer, value, node.returnPointer, isVolatile = node.isVolatile)

    def visitTypedPointerLikeReinterpretToNode(self, node: ASTTypedPointerLikeReinterpretToNode):
        type = self.visitNode(node.type)
        pointer = self.visitNode(node.pointer)
        return reducePointerLikeReinterpretToNode(ASTTypedPointerLikeReinterpretToNode(node.sourcePosition, type, pointer))

    def visitTypedPointerLikeSubscriptAtNode(self, node: ASTTypedPointerLikeSubscriptAtNode):
        type = self.visitNode(node.type)
        pointer = self.visitNode(node.pointer)
        index = self.visitNode(node.index)
        return ASTTypedPointerLikeSubscriptAtNode(node.sourcePosition, type, pointer, index)

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
        return reduceTypedOverloadedApplicationNode(ASTTypedOverloadedApplicationNode(node.sourcePosition, applicationType, overloads, argument, node.alternativeIndices))

    def visitDecoratedTypeNode(self, node: ASTDecoratedTypeNode):
        baseType = self.visitNode(node.baseType)
        return reduceDecoratedTypeNode(ASTDecoratedTypeNode(baseType, baseType))

    def visitPointerTypeNode(self, node: ASTPointerTypeNode):
        baseType = self.visitNode(node.baseType)
        return reduceDecoratedTypeNode(ASTPointerTypeNode(baseType, baseType))

    def visitReferenceTypeNode(self, node: ASTReferenceTypeNode):
        baseType = self.visitNode(node.baseType)
        return reduceDecoratedTypeNode(ASTReferenceTypeNode(baseType, baseType))

    def visitTemporaryReferenceTypeNode(self, node: ASTTemporaryReferenceTypeNode):
        baseType = self.visitNode(node.baseType)
        return reduceDecoratedTypeNode(ASTTemporaryReferenceTypeNode(baseType, baseType))

    def visitArrayTypeNode(self, node: ASTArrayTypeNode):
        elementType = self.visitNode(node.elementType)
        size = self.visitNode(node.size)
        return reduceArrayType(ASTArrayTypeNode(node.sourcePosition, elementType, size))
    
    def visitInductiveTypeNode(self, node: ASTInductiveTypeNode):
        reducedContent = self.visitNode(node.content)
        return ASTInductiveTypeNode(node.sourcePosition, node.name, node.recursiveBinding, reducedContent)
    
    def visitProductTypeNode(self, node: ASTProductTypeNode):
        reducedElementTypes = []
        for element in node.elementTypes:
            reducedElementTypes.append(self.visitNode(element))
        return reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, node.name, reducedElementTypes))

    def visitRecordTypeNode(self, node: ASTRecordTypeNode):
        reducedElementTypes = []
        for element in node.elementTypes:
            reducedElementTypes.append(self.visitNode(element))
        return reduceRecordTypeNode(ASTRecordTypeNode(node.sourcePosition, reducedElementTypes))

    def visitDictionaryTypeNode(self, node: ASTDictionaryTypeNode):
        keyType = self.visitNode(node.keyType)
        valueType = self.visitNode(node.valueType)
        return reduceDictionaryTypeNode(ASTDictionaryTypeNode(node.sourcePosition, keyType, valueType))

    def visitSumTypeNode(self, node: ASTSumTypeNode):
        reducedAlternativeTypes = []
        for alternative in node.alternativeTypesTypes:
            reducedAlternativeTypes.append(self.visitNode(alternative))
        return reduceSumTypeNode(ASTSumTypeNode(node.sourcePosition, reducedAlternativeTypes))

    def visitTypedDictionaryNode(self, node: ASTTypedDictionaryNode):
        reducedType = self.visitNode(node.type)
        reducedElements = []
        for element in node.elements:
            reducedElements.append(self.visitNode(element))
        return reduceDictionaryNode(ASTTypedDictionaryNode(node.sourcePosition, reducedType, reducedElements))

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        reducedType = self.visitNode(node.type)
        reducedElements = []
        for element in node.elements:
            reducedElements.append(self.visitNode(element))
        return reduceTupleNode(ASTTypedTupleNode(node.sourcePosition, reducedType, reducedElements, node.isRecord))

    def visitTypedInjectSumNode(self, node: ASTTypedInjectSumNode):
        reducedType = self.visitNode(node.type)
        reducedValue = self.visitNode(node.value)
        return reduceInjectSumNode(ASTTypedInjectSumNode(node.sourcePosition, reducedType, node.variantIndex, reducedValue))

    def visitTypedModifiedTupleNode(self, node: ASTTypedModifiedTupleNode):
        reducedType = self.visitNode(node.type)
        baseType = self.visitNode(node.baseTuple)

        reducedElements = []
        for element in node.elements:
            reducedElements.append(self.visitNode(element))
        return reduceModifiedTupleNode(ASTTypedModifiedTupleNode(node.sourcePosition, reducedType, baseType, reducedElements, node.elementIndices, node.isRecord))

    def visitTypedTupleAtNode(self, node: ASTTypedTupleAtNode):
        reducedType = self.visitNode(node.type)
        reducedTuple = self.visitNode(node.tuple)
        return reduceTupleAtNode(ASTTypedTupleAtNode(node.sourcePosition, reducedType, reducedTuple, node.loadResult))
    
    def visitTypedFromModuleImportNode(self, node: ASTTypedFromModuleImportNode):
        return reduceFromModuleImportNode(ASTTypedFromModuleImportNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.module), node.name))

    def visitTypedModuleExportValueNode(self, node: ASTTypedModuleExportValueNode):
        return ASTTypedModuleExportValueNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.value))

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode):
        return ASTTypedModuleEntryPointNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.entryPoint))
    
    def visitTypedFromExternalImportWithTypeNode(self, node: ASTTypedFromExternalImportWithTypeNode):
        return ASTTypedFromExternalImportWithTypeNode(node.sourcePosition, self.visitNode(node.type), node.externalName, node.name)
    
def getTypeOfAnalyzedNode(node: ASTNode, sourcePosition: SourcePosition) -> ASTNode:
    if node.isTypeNode():
        return ASTLiteralTypeNode(sourcePosition, node.getTypeUniverse())
    return node.type

def unpackReductionArgumentToArity(argument: ASTTypedTupleNode, requiredArity: int):
    if requiredArity == 0:
        return []
    elif requiredArity == 1:
        return [argument]

    if argument.isTypedTupleNode():
        return argument.elements
    
    assert False

def betaReduceFunctionalValueApplicationWithArgument(functionalValue: FunctionalValue, application: ASTTypedApplicationNode, argument: ASTNode):
    argumentBindings = functionalValue.argumentBindings
    shouldBetaReduce = len(functionalValue.captureBindings) == 0 and functionalValue.isCompileTimeReducible()
    if not shouldBetaReduce:
        return application

    unpackedArguments = unpackReductionArgumentToArity(argument, len(argumentBindings))
    body = functionalValue.body

    substitutionContext = SubstitutionContext()
    for i in range(len(unpackedArguments)):
        substitutionContext.setSubstitutionNodeForBinding(argumentBindings[i], unpackedArguments[i])
    return ASTBetaReducer(substitutionContext).visitNode(body)

def betaReduceTypedFunctionalNodeApplicationWithArgument(typedFunctionalNode: ASTTypedFunctionalNode, application: ASTTypedApplicationNode, argument: ASTNode):
    argumentBinding = typedFunctionalNode.argumentBinding
    body = typedFunctionalNode.body

    assert len(typedFunctionalNode.captureBindings) == 0

    substitutionContext = SubstitutionContext()
    substitutionContext.setSubstitutionNodeForBinding(argumentBinding, argument)
    return ASTBetaReducer(substitutionContext).visitNode(body)

def betaReduceFunctionalNodeApplicationWithArgument(functionalNode: ASTNode, application: ASTTypedApplicationNode, argument: ASTNode):
    if functionalNode.isTypedFunctionalNode():
        return betaReduceTypedFunctionalNodeApplicationWithArgument(functionalNode, application, argument)
    
    assert functionalNode.isTypedLiteralNode() or functionalNode.isLiteralTypeNode()
    return betaReduceFunctionalValueApplicationWithArgument(functionalNode.value, application, argument)
    
    
def makeTypedLiteralForValueAt(value: TypedValue, sourcePosition: SourcePosition) -> ASTNode:
    if value.isType():
        return ASTLiteralTypeNode(sourcePosition, value)
    return ASTTypedLiteralNode(sourcePosition, ASTLiteralTypeNode(sourcePosition, value.getType()), value)

def reducePrimitiveFunctionalValueApplicationWithArgumentNode(functionalValue: TypedValue, applicationNode: ASTTypedApplicationNode, argumentNode: ASTTypedNode):
    hasLiteralArgument = argumentNode.isLiteralTypeNode() or argumentNode.isTypedLiteralNode()
    if hasLiteralArgument:
        argumentValue = argumentNode.value
        if argumentValue.isProductTypeValue():
            evaluationResult = functionalValue(*argumentValue)
        else:
            evaluationResult = functionalValue(argumentValue)
        return makeTypedLiteralForValueAt(evaluationResult, applicationNode.sourcePosition)
    return applicationNode

PiValue.betaReduceApplicationWithArgumentWithArgumentNode = betaReduceFunctionalValueApplicationWithArgument
LambdaValue.betaReduceApplicationWithArgumentWithArgumentNode = betaReduceFunctionalValueApplicationWithArgument
CurriedFunctionalValue.betaReduceApplicationWithArgumentWithArgumentNode = reducePrimitiveFunctionalValueApplicationWithArgumentNode
CurryingFunctionalValue.betaReduceApplicationWithArgumentWithArgumentNode = reducePrimitiveFunctionalValueApplicationWithArgumentNode
PrimitiveFunction.betaReduceApplicationWithArgumentWithArgumentNode = reducePrimitiveFunctionalValueApplicationWithArgumentNode

def decorationsOfTypeExpression(node: ASTTypeNode) -> int:
    if node.isLiteralTypeNode() and node.value.isDecoratedType():
        return node.value.decorations
    elif node.isDecoratedTypeNode():
        return node.decorations
    return 0

def isMutableDecoratedTypeExpression(node: ASTTypeNode):
    return (decorationsOfTypeExpression(node) & DecoratedType.Mutable) != 0

def isVolatileDecoratedTypeExpression(node: ASTTypeNode):
    return (decorationsOfTypeExpression(node) & DecoratedType.Volatile) != 0
    
def decayDecorationsOfTypeExpression(node: ASTTypeNode):
    if node.isLiteralTypeNode() and node.value.isDecoratedType():
        return ASTLiteralTypeNode(node.sourcePosition, node.value.baseType)
    elif node.isDecoratedTypeNode():
        return node.baseType
    return node

def decayTypeExpression(node: ASTTypeNode):
    undecoratedNode = decayDecorationsOfTypeExpression(node)
    if undecoratedNode.isLiteralTypeNode():
        undecoratedType: TypedValue = undecoratedNode.value
        if undecoratedType.isReferenceType() or undecoratedType.isTemporaryReferenceType():
            baseType = undecoratedType.baseType
            if baseType.isDecoratedType():
                baseType = baseType.baseType
            return ASTLiteralTypeNode(undecoratedNode.sourcePosition, baseType)
    elif undecoratedNode.isReferenceTypeNode() or undecoratedNode.isTemporaryReferenceTypeNode():
        return decayDecorationsOfTypeExpression(undecoratedNode.baseType)
    return undecoratedNode

def reduceTypedApplicationNode(node: ASTTypedApplicationNode):
    if len(node.implicitValueSubstitutions) != 0:
        return ASTBetaReducer(SubstitutionContext()).visitNode(node)

    hasTypeArgument = node.argument.isTypeNode()
    hasLiteralFunctionalNode = node.functional.isLiteralTypeNode() or node.functional.isTypedLiteralNode()
    hasBetaReducibleFunctional = node.functional.isTypedLambdaNode() or node.functional.isTypedPiNode() or node.functional.isTypedLiteralReducibleFunctionalValue()

    if hasTypeArgument and hasBetaReducibleFunctional:
        return betaReduceFunctionalNodeApplicationWithArgument(node.functional, node, node.argument)

    if hasLiteralFunctionalNode and node.functional.value.isPurelyFunctional():
        functionalValue = node.functional.value
        return functionalValue.betaReduceApplicationWithArgumentWithArgumentNode(node, node.argument)

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
            alternativeArgument = node.alternativeArguments[i]
            implicitValueSubstitutions = node.alternativeImplicitValueSubstitutions[i]
            resultType = resultOverloadsType.alternativeTypes[i]
            alternativesWithApplication.append(reduceTypedApplicationNode(ASTTypedApplicationNode(node.sourcePosition, resultType, alternative, alternativeArgument, implicitValueSubstitutions)))
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
        piValue = PiValue(node.name, node.type.value, list(map(lambda n: n.binding, node.arguments)), node.isVariadic, [], [], node.body, node.sourcePosition, node.callingConvention)
        return ASTLiteralTypeNode(node.sourcePosition, piValue)
    return node

def reduceSigmaNode(node: ASTTypedSigmaNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        sigmaValue = SigmaValue(node.name, node.type.value, list(map(lambda n: n.binding, node.arguments)), node.isVariadic, [], [], node.body, node.sourcePosition)
        return ASTLiteralTypeNode(node.sourcePosition, sigmaValue)
    return node

def reduceLambdaNode(node: ASTTypedLambdaNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        lambdaValue = LambdaValue(node.name, node.type.value, list(map(lambda n: n.binding, node.arguments)), node.isVariadic, [], [], node.fixpointBinding, node.body, node.sourcePosition)
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

def reduceDecoratedTypeNode(node: ASTDecoratedTypeNode):
    if node.decorations == 0:
        return node.baseType
    if node.baseType.isLiteralTypeNode():
        return ASTLiteralTypeNode(node.sourcePosition, DecoratedType.makeWithDecorations(node.baseType.value, node.decorations))
    if node.baseType.isDecoratedTypeNode():
        return ASTDecoratedTypeNode(node.sourcePosition, node.baseType.baseType, node.decorations | node.baseType.decorations)
    return node

def reducePointerTypeNode(node: ASTPointerTypeNode):
    if node.baseType.isLiteralTypeNode():
        return ASTLiteralTypeNode(node.sourcePosition, PointerType.makeWithBaseType(node.baseType.value))
    return node

def reduceReferenceTypeNode(node: ASTPointerTypeNode):
    if node.baseType.isReferenceTypeNode():
        return node.baseType
    elif node.baseType.isTemporaryReferenceTypeNode():
        return reduceReferenceTypeNode(ASTReferenceTypeNode(node.sourcePosition, node.baseType.baseType))

    if node.baseType.isLiteralTypeNode():
        return ASTLiteralTypeNode(node.sourcePosition, ReferenceType.makeWithBaseType(node.baseType.value))
    return node

def reduceTemporaryReferenceTypeNode(node: ASTTemporaryReferenceTypeNode):
    if node.baseType.isTemporaryReferenceTypeNode():
        return node.baseType
    elif node.baseType.isReferenceTypeNode():
        return node.baseType

    if node.baseType.isLiteralTypeNode():
        return ASTLiteralTypeNode(node.sourcePosition, TemporaryReferenceType.makeWithBaseType(node.baseType.value))
    return node

def reduceArrayType(node: ASTArrayTypeNode):
    if node.elementType.isLiteralTypeNode() and node.size.isTypedLiteralNode():
        return ASTLiteralTypeNode(node.sourcePosition, ArrayType.makeWithElementTypeAndSize(node.elementType.value, node.size.value))
    return node

def reduceProductTypeNode(node: ASTProductTypeNode):
    if node.name is None:
        if len(node.elementTypes) == 0:
            return ASTLiteralTypeNode(node.sourcePosition, VoidType)
        elif len(node.elementTypes) == 1:
            return node.elementTypes[0]
    elif len(node.elementTypes) == 0:
        return ASTLiteralTypeNode(node.sourcePosition, UnitTypeClass(node.name.value, None))

    if all(elementType.isLiteralTypeNode() for elementType in node.elementTypes):
        elementTypes = list(map(lambda n: n.value, node.elementTypes))
        if node.name is not None:
            return ASTLiteralTypeNode(node.sourcePosition, ProductType(elementTypes, node.name.value))
        else:
            return ASTLiteralTypeNode(node.sourcePosition, ProductType.makeWithElementTypes(elementTypes))
    return node

def reduceRecordTypeNode(node: ASTRecordTypeNode):
    if all(elementType.isLiteralTypeNode() for elementType in node.elementTypes):
        nameValue = None
        if node.name is not None:
            nameValue = node.name.value
        return ASTLiteralTypeNode(node.sourcePosition, RecordType(list(map(lambda n: n.value, node.elementTypes)), node.fieldNames, nameValue))
    return node

def reduceSumTypeNode(node: ASTSumTypeNode):
    if len(node.alternativeTypes) == 0:
        return ASTLiteralTypeNode(node.sourcePosition, AbortType)
    elif len(node.alternativeTypes) == 1:
        return node.alternativeTypes[0]
    elif len(node.alternativeTypes) == 2:
        if node.alternativeTypes[0].isSumTypeNode():
            return reduceSumTypeNode(ASTSumTypeNode(node.sourcePosition, node.alternativeTypes[0].alternativeTypes + node.alternativeTypes[1:]))
        elif node.alternativeTypes[0].isSumTypeNodeOrLiteral():
            newAlternativeTypes = []
            for alternativeType in node.alternativeTypes[0].value.variantTypes:
                newAlternativeTypes.append(ASTLiteralTypeNode(node.sourcePosition, alternativeType))
            newAlternativeTypes += node.alternativeTypes[1:]
            return reduceSumTypeNode(ASTSumTypeNode(node.sourcePosition, newAlternativeTypes))

    if all(alternativeType.isLiteralTypeNode() for alternativeType in node.alternativeTypes):
        return ASTLiteralTypeNode(node.sourcePosition, SumType.makeWithVariantTypes(list(map(lambda n: n.value, node.alternativeTypes))))
    return node

def reduceDictionaryTypeNode(node: ASTDictionaryTypeNode):
    if node.keyType.isLiteralTypeNode() and node.valueType.isLiteralTypeNode():
        return ASTLiteralTypeNode(node.sourcePosition, DictionaryType.makeWithKeyAndValueType(node.keyType.value, node.valueType.value))
    return node

def reduceDictionaryNode(node: ASTTypedDictionaryNode):
    return node

def reduceTupleNode(node: ASTTypedTupleNode):
    if not node.isRecord:
        if len(node.elements) == 0:
            return ASTLiteralNode(node.sourcePosition, node.type, VoidType.getSingleton())
        elif len(node.elements) == 1:
            return node.elements[0]

    if node.type.isLiteralTypeNode() and all(element.isTypedLiteralNode() for element in node.elements):
        productType: ProductType = node.type.value
        tuple = productType.makeWithElements(list(map(lambda n: n.value, node.elements)))
        return ASTTypedLiteralNode(node.sourcePosition, node.type, tuple)
    return node

def reduceInjectSumNode(node: ASTTypedInjectSumNode):
    if node.type.isLiteralTypeNode() and node.value.isTypedLiteralNode():
        sumValue = node.type.value.makeWithTypeIndexAndValue(node.variantIndex, node.value.value)
        return ASTTypedLiteralNode(node.sourcePosition, node.type, sumValue)
    return node

def reduceModifiedTupleNode(node: ASTTypedModifiedTupleNode):
    return node

def reduceTupleAtNode(node: ASTTypedTupleAtNode):
    if node.loadResult:
        if node.tuple.isTypedTupleNode():
            return node.tuple.elements[node.index]
        elif node.tuple.isTypedLiteralNode():
            return ASTTypedLiteralNode(node.sourcePosition, node.type, node.tuple.value[node.index])
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

def reduceIfNode(node: ASTTypedIfNode):
    if node.condition.isTypedLiteralNode():
        if node.condition.value.interpretAsBoolean():
            return node.trueExpression
        else:
            return node.falseExpression
    return node

def reduceWhileNode(node: ASTTypedWhileNode):
    if node.condition.isTypedLiteralNode():
        if not node.condition.value.interpretAsBoolean():
            return ASTTypedLiteralNode(node.sourcePosition, node.type, VoidType.getSingleton())
    return node

def reduceDoWhileNode(node: ASTTypedDoWhileNode):
    if node.condition.isTypedLiteralNode():
        if not node.condition.value.interpretAsBoolean():
            resultValue = ASTTypedLiteralNode(node.sourcePosition, node.type, VoidType.getSingleton())
            sequence = ASTTypedSequenceNode(node.sourcePosition, node.type, [node.bodyExpression, resultValue])
    return node

def reduceArraySubscriptAtNode(node: ASTTypedArraySubscriptAtNode):
    return node

def reducePointerLikeReinterpretToNode(node: ASTTypedPointerLikeReinterpretToNode):
    if node.pointer.isTypedPointerLikeReinterpretToNode():
        return ASTTypedPointerLikeReinterpretToNode(node.sourcePosition, node.type, node.pointer.pointer)
    return node

def mergeTypeUniversesOfTypeNodePair(leftNode: ASTTypedNode, rightNode: ASTTypedNode, sourcePosition: SourcePosition) -> ASTLiteralTypeNode:
    leftUniverseIndex = leftNode.computeTypeUniverseIndex()
    rightUniverseIndex = rightNode.computeTypeUniverseIndex()
    mergedUniverse = max(leftUniverseIndex, rightUniverseIndex)
    return ASTLiteralTypeNode(sourcePosition, TypeUniverse.getWithIndex(mergedUniverse))

def mergeTypeUniversesOfTypeNodes(nodes: list[ASTTypedNode], sourcePosition: SourcePosition) -> ASTLiteralTypeNode:
    mergedUniverse = 0
    for node in nodes:
        mergedUniverse = max(mergedUniverse, node.computeTypeUniverseIndex())
    return ASTLiteralTypeNode(sourcePosition, TypeUniverse.getWithIndex(mergedUniverse))

