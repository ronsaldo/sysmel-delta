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
    
    def visitNodeWithCurrentExpectedType(self, node: ASTNode) -> ASTTypedNode | ASTTypeNode:
        return self.visitNode(node)
    
    def mergeTypesOfBranch(self, leftTypeExpression: ASTNode, rightTypeExpression: ASTNode, sourcePosition: SourcePosition):
        if leftTypeExpression.isEquivalentTo(rightTypeExpression):
            return leftTypeExpression

        return self.makeSemanticError(sourcePosition, "Type checking failure. Branch has mismatching types. '%s' vs '%s'" % (leftTypeExpression.prettyPrint(), rightTypeExpression.prettyPrint()))

    def attemptToVisitNodeWithExpectedTypeExpression(self, node: ASTNode, expectedTypeExpression: ASTNode, startingImplicitValueSubstitutions = []) -> tuple[tuple[SymbolImplicitValueBinding, ASTNode], ASTTypedNode | ASTTypeNode, str | None]:
        typedNode = self.visitNode(node)

        if expectedTypeExpression is None:
            return [], typedNode, None

        expectedTypeNode = self.visitTypeExpression(expectedTypeExpression)
        startingEnvironment = self.lexicalEnvironment
        doesTypeCheck, newEnvironment = self.withEnvironment(self.lexicalEnvironment.withImplicitValueBindingSubstitutions(startingImplicitValueSubstitutions)).doesTypedNodeConformToTypeExpression(typedNode, expectedTypeNode)
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

    def visitApplicationNode(self, node: ASTApplicationNode):
        functional = self.visitNode(node.functional)
        isImplicit = node.kind == ASTApplicationNode.Bracket

        if len(node.arguments) == 0:
            return self.visitNode(ASTArgumentApplicationNode(node.sourcePosition, functional, ASTLiteralNode(node.sourcePosition, VoidType.getSingleton()), isImplicit = isImplicit))

        for argument in node.arguments:
            functional = self.visitNode(ASTArgumentApplicationNode(argument.sourcePosition, functional, argument, isImplicit = isImplicit))
        return functional
    
    def unpackArgumentsToRequiredArity(self, argument: ASTNode, requiredArity):
        assert requiredArity >= 1
        if requiredArity == 1:
            return [argument], None
        
        if argument.isTupleNode() or argument.isTypedTupleNode():
            argumentArity = len(argument.elements)
            if argumentArity != requiredArity:
                return None, "Expected %d arguments instead of %d." % (requiredArity, argumentArity)
            return argument.elements, None
        
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
        else:
            assert piNode.isTypedPiNode()
            typedFunctionalNode: ASTTypedFunctionalNode = piNode
            argumentBindings = list(map(lambda n: n.binding, typedFunctionalNode.arguments))
            piBody = typedFunctionalNode.body

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

        unpackedArguments, errorMessage = self.unpackArgumentsToRequiredArity(argument, len(argumentBindings))
        if errorMessage is not None:
            return [], [argument], None, [], errorMessage

        implicitValueSubstitutions = []
        unpackedTypedArguments = []
        for i in range(len(argumentBindings)):
            argumentBinding = argumentBindings[i]
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
            acceptedAlternativeImplicitValueSubstitutions = []
            index = 0
            typedArgument = self.visitNode(node.argument)
            for alternativeType in functional.type.alternativeTypes:
                pendingInferenceArguments, alternativeTypedArgument, resultType, implicitValueSubstitutions, errorMessage = self.attemptBetaReducePiWithTypedArgument(alternativeType, typedArgument, isImplicitApplication = node.isImplicit)
                assert len(pendingInferenceArguments) == 0
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
        
        return ASTTypedModuleExportValueNode(node.sourcePosition, value.type, externalName, name, value, self.lexicalEnvironment.lookModule())

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

    def visitArgumentNode(self, node: ASTArgumentNode):
        assert False

    def visitBinaryExpressionSequenceNode(self, node: ASTBinaryExpressionSequenceNode):
        if len(node.elements) == 3:
            return self.visitNode(ASTMessageSendNode(node.sourcePosition, node.elements[0], node.elements[1], [node.elements[2]]))
        assert False

    def visitErrorNode(self, node: ASTErrorNode):
        errorNode = ASTTypedErrorNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, AbortType), node.message, [])
        self.errorAccumulator.add(errorNode)
        return errorNode

    def visitFunctionNode(self, node: ASTFunctionNode):
        functionalTypeNode = self.visitNodeForMacroExpansionOnly(node.functionalType)
        if not functionalTypeNode.isFunctionalDependentTypeNode():
            functionalTypeNode = self.makeSemanticError(functionalTypeNode.sourcePosition, 'Expected a function type expression.', functionalTypeNode)
        if functionalTypeNode.isTypedErrorNode():
           return self.visitNode(ASTSequenceNode(node.sourcePosition, [functionalTypeNode, node.body]))
        
        if len(functionalTypeNode.arguments) == 0 and len(functionalTypeNode.tupleArguments) == 0:
            return self.visitNode(ASTLambdaNode(node.sourcePosition, False, None, None, functionalTypeNode.resultType, node.body, functionalTypeNode.callingConvention))

        resultType = functionalTypeNode.resultType
        body = node.body
        if len(functionalTypeNode.tupleArguments) != 0:
            body = ASTLambdaNode(node.sourcePosition, functionalTypeNode.tupleArguments, resultType, body)
            resultType = None

        for argument in reversed(functionalTypeNode.arguments):
            body = ASTLambdaNode(argument.sourcePosition, [argument], resultType, body)
            resultType = None

        ## Set the calling convention on the last lambda.
        body.callingConvention = functionalTypeNode.callingConvention
        return self.visitNode(body)
    
    def visitFunctionTypeNode(self, node: ASTFunctionTypeNode):
        argumentType = self.visitTypeExpression(node.argumentType)
        resultType = self.visitTypeExpression(node.resultType)
        typeUniverse = mergeTypeUniversesOfTypeNodePair(argumentType, resultType, node.sourcePosition)
        return reduceFunctionTypeNode(ASTTypedFunctionTypeNode(node.sourcePosition, typeUniverse, argumentType, resultType))

    def visitFunctionalDependentTypeNode(self, node: ASTFunctionalDependentTypeNode):
        if len(node.arguments) == 0 and len(node.tupleArguments) == 0:
            return self.visitNode(ASTPiNode(node.sourcePosition, [], node.resultType, node.callingConvention))

        resultType = node.resultType
        if len(node.tupleArguments) != 0:
            resultType = ASTPiNode(node.sourcePosition, node.tupleArguments, resultType)

        for argument in reversed(node.arguments):
            if argument.isExistential:
                resultType = ASTSigmaNode(argument.sourcePosition, [argument], resultType)
            else:
                resultType = ASTPiNode(argument.sourcePosition, [argument], resultType)
        return self.visitNode(resultType)
    
    def analyzeIdentifierReferenceNodeWithBinding(self, node: ASTIdentifierReferenceNode, binding: SymbolBinding) -> ASTTypedNode | ASTTypeNode:
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

    def visitFormProductTypeNode(self, node: ASTFormProductTypeNode):
        assert False

    def visitFormSumTypeNode(self, node: ASTFormSumTypeNode):
        assert False

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

    def analyzeArgumentNode(self, node: ASTArgumentNode) -> ASTTypedArgumentNode:
        assert node.isArgumentNode()
        name = self.evaluateOptionalSymbol(node.nameExpression)
        type = self.visitOptionalTypeExpression(node.typeExpression)
        binding = SymbolArgumentBinding(node.sourcePosition, name, type, isImplicit = node.isImplicit)
        return ASTTypedArgumentNode(node.sourcePosition, type, binding, node.isImplicit, node.isExistential)

    def visitLambdaNode(self, node: ASTLambdaNode):
        functionalEnvironment = FunctionalAnalysisEnvironment(self.lexicalEnvironment, [], node.sourcePosition)
        typedArguments = []
        for argument in node.arguments:
            typedArgument = self.withEnvironment(functionalEnvironment).analyzeArgumentNode(argument)
            functionalEnvironment = functionalEnvironment.withArgumentBinding(typedArgument.binding)
            typedArguments.append(typedArgument)

        body = self.withEnvironment(functionalEnvironment).visitNodeWithExpectedTypeExpression(node.body, node.resultType)

        ## Compute the lambda type.
        bodyType = getTypeOfAnalyzedNode(body, node.sourcePosition)
        typeUniverse = mergeTypeUniversesOfTypeNodes([body] + list(map(lambda a: a.type, typedArguments)), node.sourcePosition)
        typedPi = reducePiNode(ASTTypedPiNode(node.sourcePosition, typeUniverse, typedArguments, functionalEnvironment.captureBindings, bodyType, node.callingConvention))

        ## Make the lambda node.
        typedLambda = ASTTypedLambdaNode(node.sourcePosition, typedPi, typedArguments, functionalEnvironment.captureBindings, body, node.callingConvention)
        return reduceLambdaNode(typedLambda)

    def visitPiNode(self, node: ASTPiNode):
        functionalEnvironment = FunctionalAnalysisEnvironment(self.lexicalEnvironment, [], node.sourcePosition)
        typedArguments = []
        for argument in node.arguments:
            typedArgument = self.withEnvironment(functionalEnvironment).analyzeArgumentNode(argument)
            functionalEnvironment = functionalEnvironment.withArgumentBinding(typedArgument.binding)
            typedArguments.append(typedArgument)

        body = self.withEnvironment(functionalEnvironment).visitTypeExpression(node.body)
        typeUniverse = mergeTypeUniversesOfTypeNodes([body] + list(map(lambda a: a.type, typedArguments)), node.sourcePosition)
        typedPi = ASTTypedPiNode(node.sourcePosition, typeUniverse, typedArguments, functionalEnvironment.captureBindings, body, node.callingConvention)
        return reducePiNode(typedPi)

    def visitSigmaNode(self, node: ASTSigmaNode):
        functionalEnvironment = FunctionalAnalysisEnvironment(self.lexicalEnvironment, [], node.sourcePosition)
        typedArguments = []
        for argument in node.arguments:
            typedArgument = self.withEnvironment(functionalEnvironment).analyzeArgumentNode(argument)
            functionalEnvironment = functionalEnvironment.withArgumentBinding(typedArgument.binding)
            typedArguments.append(typedArgument)

        body = self.withEnvironment(functionalEnvironment).visitTypeExpression(node.body)
        typeUniverse = mergeTypeUniversesOfTypeNodes([body] + list(map(lambda a: a.type, typedArguments)), node.sourcePosition)
        typedSigma = ASTTypedSigmaNode(node.sourcePosition, typeUniverse, typedArguments, functionalEnvironment.captureBindings, body, node.callingConvention)
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
            if analyzedReceiver is not None and not analyzedReceiver.isLiteralTypeNode():
                if analyzedReceiver.type.isReferenceLikeTypeNodeOrLiteral():
                    if selector in ReferenceLikeTypeMacros:
                        return self.expandMessageSendWithMacro(node, analyzedReceiver, ReferenceLikeTypeMacros[selector])
                if analyzedReceiver.type.isPointerTypeNodeOrLiteral():
                    if selector in PointerTypeMacros:
                        return self.expandMessageSendWithMacro(node, analyzedReceiver, PointerTypeMacros[selector])

                ## Getter.
                if len(node.arguments) == 0:
                    fieldIndex, fieldType = analyzedReceiver.type.findIndexOfFieldOrNoneAt(selector, node.sourcePosition)
                    if fieldIndex is not None:
                        return reduceTupleAtNode(ASTTypedTupleAtNode(node.sourcePosition, fieldType, analyzedReceiver, fieldIndex))

            selectorNode = ASTIdentifierReferenceNode(node.selector.sourcePosition, selector)
        else:
            selectorNode = errorNode
        
        if analyzedReceiver is None:
            return self.visitNode(ASTApplicationNode(node.sourcePosition, selectorNode, self.packMessageSendArguments(node.sourcePosition, node.arguments)))
        else:
            return self.visitNode(ASTApplicationNode(node.sourcePosition, selectorNode, self.packMessageSendArguments(node.sourcePosition, [analyzedReceiver] + node.arguments)))

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

            resultType = typedExpression.type
            typedElements.append(typedExpression)

        if len(typedElements) == 1:
            return typedElements[0]
        return ASTTypedSequenceNode(node.sourcePosition, resultType, typedElements)

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
        assert False

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
            return reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, typedElements))
        
        tupleType = reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, elementTypeExpressions))
        return reduceTupleNode(ASTTypedTupleNode(node.sourcePosition, tupleType, typedElements))

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

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitSumTypeNode(self, node: ASTProductTypeNode):
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
        assert False

    def visitTypedOverloadedApplicationNode(self, node: ASTTypedOverloadedApplicationNode):
        return node

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode):
        return node

    def visitTypedPointerLikeLoadNode(self, node: ASTTypedPointerLikeLoadNode):
        return node

    def visitTypedPointerLikeStoreNode(self, node: ASTTypedPointerLikeStoreNode):
        return node

    def visitTypedPointerLikeReinterpretToNode(self, node: ASTTypedPointerLikeReinterpretToNode):
        return node

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode):
        return node

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        return node
    
    def visitTypedTupleAtNode(self, node: ASTTypedTupleAtNode):
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
        return reducePiNode(ASTTypedPiNode(node.sourcePosition, newType, newArguments, newCaptureBindings, reducedBody, node.callingConvention))

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

        reducedBody = reducer.visitNode(node.body)
        return reduceLambdaNode(ASTTypedLambdaNode(node.sourcePosition, newType, newArguments, newCaptureBindings, reducedBody, node.callingConvention))

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode):
        newType = self.visitNode(node.type)
        reducer, newArguments, newCaptureBindings = self.reduceArguments(node.arguments, node.captureBindings)

        reducedBody = reducer.visitNode(node.body)
        return reduceSigmaNode(ASTTypedSigmaNode(node.sourcePosition, newType, newArguments, newCaptureBindings, reducedBody, node.callingConvention))

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        return node

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode):
        assert False

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
        return reduceTupleNode(ASTTypedTupleNode(node.sourcePosition, reducedType, reducedElements))
    
    def visitTypedTupleAtNode(self, node: ASTTypedTupleAtNode):
        reducedType = self.visitNode(node.type)
        reducedTuple = self.visitNode(node.tuple)
        return reduceTupleAtNode(ASTTypedTupleAtNode(node.sourcePosition, reducedType, reducedTuple))
    
    def visitTypedFromModuleImportNode(self, node: ASTTypedFromModuleImportNode):
        return reduceFromModuleImportNode(ASTTypedFromModuleImportNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.module), node.name))

    def visitTypedModuleExportValueNode(self, node: ASTTypedModuleExportValueNode):
        return ASTTypedModuleExportValueNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.value))

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode):
        return ASTTypedModuleEntryPointNode(node.sourcePosition, self.visitNode(node.type), self.visitNode(node.entryPoint))
    
    def visitTypedFromExternalImportWithTypeNode(self, node: ASTTypedFromExternalImportWithTypeNode):
        return ASTTypedFromExternalImportWithTypeNode(node.sourcePosition, self.visitNode(node.type), node.externalName, node.name)
    
def getTypeOfAnalyzedNode(node: ASTTypedNode | ASTTypeNode, sourcePosition: SourcePosition) -> ASTTypedNode | ASTTypeNode:
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

def betaReduceFunctionalValueApplicationWithArgument(functionalValue: FunctionalValue | ASTTypeNode, application: ASTTypedApplicationNode, argument: ASTTypedNode | ASTTypeNode):
    argumentBindings = functionalValue.argumentBindings
    unpackedArguments = unpackReductionArgumentToArity(argument, len(argumentBindings))
    body = functionalValue.body
    assert len(functionalValue.captureBindings) == 0

    substitutionContext = SubstitutionContext()
    for i in range(len(unpackedArguments)):
        substitutionContext.setSubstitutionNodeForBinding(argumentBindings[i], unpackedArguments[i])
    return ASTBetaReducer(substitutionContext).visitNode(body)

def betaReduceTypedFunctionalNodeApplicationWithArgument(typedFunctionalNode: ASTTypedFunctionalNode, application: ASTTypedApplicationNode, argument: ASTTypedNode | ASTTypeNode):
    argumentBinding = typedFunctionalNode.argumentBinding
    body = typedFunctionalNode.body

    assert len(typedFunctionalNode.captureBindings) == 0

    substitutionContext = SubstitutionContext()
    substitutionContext.setSubstitutionNodeForBinding(argumentBinding, argument)
    return ASTBetaReducer(substitutionContext).visitNode(body)

def betaReduceFunctionalNodeApplicationWithArgument(functionalNode: ASTTypedNode | ASTTypeNode, application: ASTTypedApplicationNode, argument: ASTTypedNode | ASTTypeNode):
    if functionalNode.isTypedFunctionalNode():
        return betaReduceTypedFunctionalNodeApplicationWithArgument(functionalNode, application, argument)
    
    assert functionalNode.isTypedLiteralNode() or functionalNode.isLiteralTypeNode()
    return betaReduceFunctionalValueApplicationWithArgument(functionalNode.value, application, argument)
    
    
def makeTypedLiteralForValueAt(value: TypedValue, sourcePosition: SourcePosition) -> ASTTypedLiteralNode | ASTTypeNode:
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
        piValue = PiValue(node.type.value, list(map(lambda n: n.binding, node.arguments)), [], [], node.body, node.sourcePosition, node.callingConvention)
        return ASTLiteralTypeNode(node.sourcePosition, piValue)
    return node

def reduceSigmaNode(node: ASTTypedPiNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        sigmaValue = SigmaValue(node.type.value, list(map(lambda n: n.binding, node.arguments)), [], [], node.body, node.sourcePosition)
        return ASTLiteralTypeNode(node.sourcePosition, sigmaValue)
    return node

def reduceLambdaNode(node: ASTTypedLambdaNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        lambdaValue = LambdaValue(node.type.value, list(map(lambda n: n.binding, node.arguments)), [], [], node.body, node.sourcePosition)
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
    if len(node.elementTypes) == 0:
        return ASTLiteralTypeNode(node.sourcePosition, VoidType)
    elif len(node.elementTypes) == 1:
        return node.elementTypes[0]

    if all(elementType.isLiteralTypeNode() for elementType in node.elementTypes):
        return ASTLiteralTypeNode(node.sourcePosition, ProductType.makeWithElementTypes(list(map(lambda n: n.value, node.elementTypes))))
    return node

def reduceTupleNode(node: ASTTypedTupleNode):
    if len(node.elements) == 0:
        return ASTLiteralNode(node.sourcePosition, node.type, VoidType.getSingleton())
    elif len(node.elements) == 1:
        return node.elements[0]

    if node.type.isLiteralTypeNode() and all(element.isTypedLiteralNode() for element in node.elements):
        productType: ProductType = node.type.value
        tuple = productType.makeWithElements(list(map(lambda n: n.value, node.elements)))
        return ASTTypedLiteralNode(node.sourcePosition, node.type, tuple)
    return node

def reduceTupleAtNode(node: ASTTypedTupleAtNode):
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

def reduceSumTypeNode(node: ASTSumTypeNode):
    if len(node.alternativeTypes) == 0:
        return ASTLiteralTypeNode(node.sourcePosition, AbortType)
    elif len(node.alternativeTypes) == 1:
        return node.alternativeTypes[0]
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

