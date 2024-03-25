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
            return ASTLiteralTypeNode(node.sourcePosition, VoidType)

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
        errorNode = ASTTypedErrorNode(sourcePosition, ASTLiteralTypeNode(sourcePosition, VoidType), errorMessage, innerNodes)
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
            return self.visitNode(ASTLiteralNode(sourcePosition), UnitType.getSingleton())
        elif len(arguments) == 1:
            return arguments[0]
        return self.visitNode(ASTTupleNode(sourcePosition, arguments))

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
            argumentBindings = piValue.argumentBindings
            piBody = piValue.body
        else:
            assert piNode.isTypedPiNode()
            typedFunctionalNode: ASTTypedFunctionalNode = piNode
            argumentBindings = typedFunctionalNode.argumentBindings
            piBody = typedFunctionalNode.body

        ## If there are zero arguments, the argument must be unit.
        if len(argumentBindings) == 0:
            implicitValueSubstitutions, typedArgument, errorMessage = self.attemptToVisitNodeWithExpectedType(argument, UnitType)
            if errorMessage is not None:
                return None, typedArgument, None, implicitValueSubstitutions, errorMessage
            return piBody

        firstArgumentBinding = argumentBindings[0]
        if isImplicitApplication and not firstArgumentBinding.isImplicit:
            return None, self.visitNode(argument), None, [], "Unexpected implicit argument application, when an explicit argument of type %s is required." % firstArgumentBinding.getTypeExpression().prettyPrint()
        
        unpackedArguments, errorMessage = self.unpackArgumentsToRequiredArity(argument, len(argumentBindings))
        if errorMessage is not None:
            return None, [argument], None, [], errorMessage

        ## Are we missing implicit arguments that need to be inferred?
        if firstArgumentBinding.isImplicit and not isImplicitApplication:
            assert False
            placeHolderBinding = SymbolImplicitValueBinding(argument.sourcePosition, argumentBinding.name, argumentBinding.getTypeExpression())
            implicitArgumentValueNode = ASTTypedIdentifierReferenceNode(argument.sourcePosition, placeHolderBinding.typeExpression, placeHolderBinding)

            substitutionContext.setSubstitutionNodeForBinding(argumentBinding, implicitArgumentValueNode)
            reduced = ASTBetaReducer(substitutionContext).visitNode(piBody)
            return implicitArgumentValueNode, argument, reduced, [], None

        implicitValueSubstitutions = []
        unpackedTypedArguments = []
        for i in range(len(argumentBindings)):
            argumentBinding = argumentBindings[i]
            implicitValueSubstitutions, unpackedTypedArgument, errorMessage = self.attemptToVisitNodeWithExpectedTypeExpression(unpackedArguments[i], argumentBinding.getTypeExpression(), implicitValueSubstitutions)
            if errorMessage is not None:
                return None, typedArgument, None, implicitValueSubstitutions, errorMessage

            substitutionContext.setSubstitutionNodeForBinding(argumentBinding, unpackedTypedArgument)
            unpackedTypedArguments.append(unpackedTypedArgument)

        reduced = ASTBetaReducer(substitutionContext).visitNode(piBody)
        return None, self.packArguments(unpackedTypedArguments, argument.sourcePosition), reduced, implicitValueSubstitutions, errorMessage
    
    def unpackArgumentsForMacro(self, macroValue: TypedValue, node: ASTNode, sourcePosition: SourcePosition):
        macroType = macroValue.getType()
        if not macroType.argumentType.isProductType():
            return node, None
        
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
            return ASTTypedApplicationNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, VoidType), functional, self.visitNode(node.argument), [])
        
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
        errorNode = ASTTypedErrorNode(node.sourcePosition, ASTLiteralTypeNode(node.sourcePosition, VoidType), node.message, [])
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
            trueExpression = ASTLiteralNode(node.sourcePosition, UnitType.getSingleton())
        trueExpression = self.visitNodeWithCurrentExpectedType(trueExpression)

        falseExpression = node.falseExpression
        if falseExpression is None:
            falseExpression = ASTLiteralNode(node.sourcePosition, UnitType.getSingleton())
        falseExpression = self.visitNodeWithCurrentExpectedType(falseExpression)

        type = self.mergeTypesOfBranch(getTypeOfAnalyzedNode(trueExpression, trueExpression.sourcePosition), getTypeOfAnalyzedNode(falseExpression, falseExpression.sourcePosition), node.sourcePosition)
        ifNode = ASTTypedIfNode(node.sourcePosition, type, condition, trueExpression, falseExpression)
        return reduceIfNode(ifNode)
    
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
        typedPi = reducePiNode(ASTTypedPiNode(node.sourcePosition, typeUniverse, functionalEnvironment.arguments, functionalEnvironment.captureBindings, bodyType, node.callingConvention))

        ## Make the lambda node.
        typedLambda = ASTTypedLambdaNode(node.sourcePosition, typedPi, functionalEnvironment.arguments, functionalEnvironment.captureBindings, body, node.callingConvention)
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
        typedPi = ASTTypedPiNode(node.sourcePosition, typeUniverse, functionalEnvironment.arguments, functionalEnvironment.captureBindings, body, node.callingConvention)
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
        typedSigma = ASTTypedSigmaNode(node.sourcePosition, typeUniverse, functionalEnvironment.arguments, functionalEnvironment.captureBindings, body, node.callingConvention)
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

    def packMessageSendArguments(self, sourcePosition: SourcePosition, arguments: list[ASTNode]):
        if len(arguments) <= 1:
            return arguments
        return [ASTTupleNode(sourcePosition, arguments)]
    
    def visitMessageSendNode(self, node: ASTMessageSendNode):
        analyzedReceiver = None
        if node.receiver is not None:
            analyzedReceiver = self.visitNode(node.receiver)

        selector, errorNode = self.evaluateSymbol(node.selector)
        if selector is not None:
            if analyzedReceiver is not None and not analyzedReceiver.isLiteralTypeNode():
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

        if all(isLiteralTypeOfTypeNode(elementType) for elementType in elementTypeExpressions):
            return reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, typedElements))
        
        tupleType = reduceProductTypeNode(ASTProductTypeNode(node.sourcePosition, elementTypeExpressions))
        return reduceTupleNode(ASTTypedTupleNode(node.sourcePosition, tupleType, typedElements))

    def visitOverloadsTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        return node

    def visitSumTypeNode(self, node: ASTProductTypeNode):
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

    def visitTypedPiNode(self, node: ASTTypedPiNode):
        assert False
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

    def visitTypedIfNode(self, node: ASTTypedIfNode):
        type = self.visitNode(node.type)
        condition = self.visitNode(node.condition)
        trueExpression = self.visitNode(node.trueExpression)
        falseExpression = self.visitNode(node.falseExpression)
        return reduceIfNode(ASTTypedIfNode(node.sourcePosition, node.type, condition, trueExpression, falseExpression))

    def visitTypedImplicitValueNode(self, node):
        return node
    
    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        assert False
        argumentBinding = node.argumentBinding
        newArgumentBinding = SymbolArgumentBinding(argumentBinding.sourcePosition, argumentBinding.name, self.visitNode(argumentBinding.typeExpression))
        newType = self.visitNode(node.type)
        
        bodyContext = SubstitutionContext(self.substitutionContext)
        bodyContext.setSubstitutionBindingForBinding(argumentBinding, newArgumentBinding)
        bodyContext.addSubstitutionsForCaptureBindings(node.captureBindings)

        reducedBody = ASTBetaReducer(bodyContext).visitNode(node.body)
        return reduceLambdaNode(ASTTypedLambdaNode(node.sourcePosition, newType, newArgumentBinding, bodyContext.captureBindings, reducedBody))

    def visitTypedSigmaNode(self, node: ASTTypedLambdaNode):
        assert False
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
        functionalValue = node.functional.value
        argumentValue = node.argument.value
        if argumentValue.isProductTypeValue():
            evaluationResult = functionalValue(*argumentValue)
        else:
            evaluationResult = functionalValue(argumentValue)
        return makeTypedLiteralForValueAt(evaluationResult, node.sourcePosition)

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
        piValue = PiValue(node.type.value, node.arguments, [], [], node.body, node.sourcePosition, node.callingConvention)
        return ASTLiteralTypeNode(node.sourcePosition, piValue)
    return node

def reduceSigmaNode(node: ASTTypedPiNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        sigmaValue = SigmaValue(node.type.value, node.arguments, [], [], node.body, node.sourcePosition)
        return ASTLiteralTypeNode(node.sourcePosition, sigmaValue)
    return node

def reduceLambdaNode(node: ASTTypedLambdaNode):
    if len(node.captureBindings) == 0 and node.type.isLiteralTypeNode():
        lambdaValue = LambdaValue(node.type.value, node.arguments, [], [], node.body, node.sourcePosition)
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

    if all(elementType.isLiteralTypeNode() for elementType in node.elementTypes):
        return ASTLiteralTypeNode(node.sourcePosition, ProductType.makeWithElementTypes(list(map(lambda n: n.value, node.elementTypes))))
    return node

def reduceTupleNode(node: ASTTypedTupleNode):
    if len(node.elements) == 0:
        return ASTLiteralNode(node.sourcePosition, node.type, UnitType.getSingleton())
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
        return ASTLiteralTypeNode(node.sourcePosition, VoidType)
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

