from .mop import *
from .syntax import *
from .asg import *
from .environment import *

class ASGBetaSubstitutionContext:
    def __init__(self) -> None:
        self.substitutionTable = {}

    def setSubstitutionForNode(self, oldNode: ASGNode, replacedNode: ASGNode):
        self.substitutionTable[oldNode] = replacedNode

    def getSubstitutionFor(self, node):
        return self.substitutionTable.get(node, node)

    def isEmpty(self) -> bool:
        return len(self.substitutionTable) == 0
    
    def includesNode(self, node) -> bool:
        return node in self.substitutionTable
    
    def includesAnyOf(self, listOfNodes) -> bool:
        for node in listOfNodes:
            if self.includesNode(node):
                return True
        return False

class ASGReductionAlgorithm(ASGDynamicProgrammingReductionAlgorithm):
    @asgPatternMatchingOnNodeKind(ASGApplicationNode, when = lambda n: n.isLiteralAlwaysReducedPrimitiveApplication() or n.isLiteralPureCompileTimePrimitiveApplication())
    def reduceLiteralApplicationNode(self, node: ASGApplicationNode) -> ASGNode:
        return node.functional.reduceApplicationWithAlgorithm(node, self)
    
    @asgPatternMatchingOnNodeKind(ASGOverloadedAlternativeSelectionNode, when = lambda n: n.alternatives.isOverloadedAlternativesNode())
    def reduceOverloadedAlternativeSelectionNode(self, node: ASGOverloadedAlternativeSelectionNode) -> ASGTypecheckedNode:
        return node.alternatives.alternatives[node.index]

    @asgPatternMatchingOnNodeKind(ASGTupleAtNode, when = lambda n: n.tuple.isTupleNode())
    def reduceTupleAt(self, node: ASGTupleAtNode) -> ASGTypecheckedNode:
        return node.tuple.elements[node.index]

class ASGBetaSubstitutionAlgorithm(ASGDynamicProgrammingAlgorithm):
    def __init__(self, substitutionContext: ASGBetaSubstitutionContext, builder: ASGBuilderWithGVN) -> None:
        super().__init__()
        self.substitutionContext = substitutionContext
        self.builder = builder

    def expandNode(self, node: ASGNode):
        if self.substitutionContext.isEmpty():
            return node
        
        if self.substitutionContext.includesNode(node):
            return self.substitutionContext.getSubstitutionFor(node)
        
        betaReplaceableDependencies = node.betaReplaceableDependencies()
        if not self.substitutionContext.includesAnyOf(betaReplaceableDependencies):
            return node

        return self(node)

    @asgPatternMatchingOnNodeKind(ASGBetaReplaceableNode)
    def expandBetaReplaceableNode(self, node: ASGBetaReplaceableNode) -> ASGTypecheckedNode:
        if not self.substitutionContext.includesNode(node):
            return self.expandGenericNodeRecursively(node)
        else:
            return self.substitutionContext.getSubstitutionFor(node)
        
    def expandParameter(self, parameter):
        if isinstance(parameter, ASGNode):
            return self.expandNode(parameter)
        elif isinstance(parameter, tuple):
            return tuple(map(self.expandParameter, parameter))
        else:
            return parameter

    @asgPatternMatchingOnNodeKind(ASGNode)
    def expandGenericNode(self, node: ASGNode) -> ASGTypecheckedNode:
        return self.expandGenericNodeRecursively(node)
    
    def expandGenericNodeRecursively(self, node: ASGNode):
        nodeAttributes = node.getAllConstructionAttributes()
        expandedParameters = []
        for attribute in nodeAttributes:
            expandedParameters.append(self.expandParameter(attribute))
        return node.__class__(*expandedParameters)

class ASGTypecheckingErrorAcumulator:
    def __init__(self) -> None:
        self.errorList = []

    def addError(self, error: ASGErrorNode):
        self.errorList.append(error)

class ASGExpandAndTypecheckingAlgorithm(ASGDynamicProgrammingAlgorithm):
    def __init__(self, environment: ASGEnvironment, builder: ASGBuilderWithGVNAndEnvironment = None, reductionAlgorithm: ASGReductionAlgorithm = None, errorAccumulator = None) -> None:
        super().__init__()
        self.environment = environment
        self.builder = builder
        self.reductionAlgorithm = reductionAlgorithm
        self.errorAccumulator = errorAccumulator
        if self.builder is None:
            self.builder = ASGBuilderWithGVNAndEnvironment(None, self.environment.getTopLevelTargetEnvironment())
        if self.reductionAlgorithm is None:
            self.reductionAlgorithm = ASGReductionAlgorithm()
        if self.errorAccumulator is None:
            self.errorAccumulator = ASGTypecheckingErrorAcumulator()

    def withDivergingEnvironment(self, newEnvironment: ASGEnvironment):
        return ASGExpandAndTypecheckingAlgorithm(newEnvironment, ASGBuilderWithGVNAndEnvironment(self.builder, newEnvironment.getTopLevelTargetEnvironment()), self.reductionAlgorithm, self.errorAccumulator)

    def withFunctionalAnalysisEnvironment(self, newEnvironment: ASGFunctionalAnalysisEnvironment):
        return self.withDivergingEnvironment(newEnvironment)

    def postProcessResult(self, result):
        return self.reductionAlgorithm(result.asASGNode())
    
    def withChildLexicalEnvironmentDo(self, newEnvironment: ASGEnvironment, aBlock):
        oldEnvironment = self.environment
        self.environment = newEnvironment
        try:
            return aBlock()
        finally:
            self.environment = oldEnvironment

    def syntaxPredecessorOf(self, node: ASGSyntaxNode):
        predecessor = node.syntacticPredecessor
        if predecessor is not None:
            return self(predecessor)
        else:
            return None
        
    def attemptExpansionOfNode(self, node: ASGNode) -> tuple[ASGNode, list[ASGNode]]:
        builderMemento = self.builder.memento()
        errorMemento = self.errorAccumulator

        self.errorAccumulator = ASGTypecheckingErrorAcumulator()
        expansionResult = self(node)
        expansionErrors = self.errorAccumulator.errorList
        self.errorAccumulator = errorMemento

        if len(expansionErrors) != 0:
            self.builder.restoreMemento(builderMemento)

        return expansionResult, expansionErrors
        
    def makeErrorAtNode(self, message: str, node: ASGNode) -> ASGTypecheckedNode:
        type = self.builder.topLevelIdentifier('Abort')
        innerNodes = []
        if not node.isSyntaxNode():
            innerNodes = [node]
        errorNode = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGErrorNode, type, message, innerNodes)
        self.errorAccumulator.addError(errorNode.asASGDataNode())
        return errorNode
    
    def analyzeNodeWithExpectedType(self, node: ASGNode, expectedType: ASGNode) -> ASGTypecheckedNode:
        analyzedNode = self(node).asASGDataNode()
        if expectedType is None:
            return analyzedNode, True

        # Coercion
        expectedTypeNode = expectedType.asASGTypeNode()
        analyzedNode = expectedTypeNode.coerceExpressionWith(analyzedNode, self)

        # Type checking
        analyzedNodeType = analyzedNode.getTypeInEnvironment(self.environment)
        if expectedTypeNode.isSatisfiedAsTypeBy(analyzedNodeType):
            return analyzedNode, True
        return self.makeErrorAtNode('Type checking failure. Expected %s instead of %s.' % (expectedType.prettyPrintNameWithDataAttributes(), analyzedNodeType.prettyPrintNameWithDataAttributes()), analyzedNode), False

    def evaluateSymbol(self, node: ASGNode) -> str:
        typecheckedNode, typechecked = self.analyzeNodeWithExpectedType(node, self.builder.topLevelIdentifier('Symbol'))
        if not typechecked:
            return None
        
        typecheckedNode = typecheckedNode.asASGDataNode()
        if typecheckedNode.isLiteralNode():
            return typecheckedNode.value

        self.makeErrorAtNode('Expected a literal symbol.', node)
        return None

    def evaluateOptionalSymbol(self, node: ASGNode) -> str:
        if node is None:
            return None
        
        return self.evaluateSymbol(node)
    
    def analyzeArgumentNode(self, functionalAnalyzer, node: ASGNode, index: int) -> ASGArgumentNode:
        if not node.isKindOf(ASGSyntaxBindableNameNode):
            return self.makeErrorAtNode('Expected a bindable name node for defining the argument.', node)
        
        # The first argument name and types are in the context of the parent.
        argumentAnalyzer = self
        if index != 0:
            argumentAnalyzer = functionalAnalyzer

        bindableName: ASGSyntaxBindableNameNode = node
        type = argumentAnalyzer.analyzeOptionalTypeExpression(bindableName.typeExpression)
        if type is None:
            type = argumentAnalyzer.builder.topLevelIdentifier('Any')

        name = argumentAnalyzer.evaluateOptionalSymbol(bindableName.nameExpression)
        return functionalAnalyzer.builder.forSyntaxExpansionBuild(functionalAnalyzer, node, ASGArgumentNode, type, index, name, isImplicit = bindableName.isImplicit).asASGDataNode()

    def analyzeTypeExpression(self, node: ASGNode) -> ASGTypecheckedNode:
        analyzedNode = self(node).asASGTypeNode()
        if analyzedNode.isTypeNode():
            return analyzedNode

        return self.makeErrorAtNode('Expected a type expression.', node)

    def analyzeOptionalTypeExpression(self, node: ASGNode) -> ASGTypecheckedNode:
        if node is None:
            return None
        return self.analyzeTypeExpression(node)
    
    def expandMacrosOnly(self, node: ASGNode) -> ASGNode:
        # TODO: Implement this properly.
        return node
    
    def emitBoundsSize(self, node: ASGNode, index: ASGNode, size: ASGNode) -> ASGNode:
        self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGBoundsCheckNode, index, size, predecessor = self.builder.currentPredecessor)

    @asgPatternMatchingOnNodeKind(ASGSyntaxErrorNode)
    def expandSyntaxErrorNode(self, node: ASGSyntaxErrorNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        return self.makeErrorAtNode(node.message, node)

    @asgPatternMatchingOnNodeKind(ASGSyntaxAssignmentNode)
    def expandSyntaxAssignmentNode(self, node: ASGSyntaxAssignmentNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        store = self.expandMacrosOnly(node.store)
        derivation = ASGNodeSyntaxExpansionDerivation(self, node)
        if store.isKindOf(ASGSyntaxFunctionalDependentTypeNode):
            functionalDependentNode: ASGSyntaxFunctionalDependentTypeNode = store
            return self.fromNodeContinueExpanding(node, ASGSyntaxFunctionNode(derivation, None, functionalDependentNode, node.value))
        elif store.isKindOf(ASGSyntaxBindableNameNode):
            bindableNameNode: ASGSyntaxBindableNameNode = store
            if bindableNameNode.typeExpression is not None and bindableNameNode.typeExpression.isKindOf(ASGSyntaxFunctionalDependentTypeNode):
                functionalDependentNode: ASGSyntaxFunctionalDependentTypeNode = bindableNameNode.typeExpression
                function = self(ASGSyntaxFunctionNode(derivation, bindableNameNode.nameExpression, functionalDependentNode, node.value, isFixpoint = bindableNameNode.hasPostTypeExpression))
                return self.fromNodeContinueExpanding(node, ASGSyntaxBindingDefinitionNode(derivation, None, bindableNameNode.nameExpression, function))
            else:
                return self.fromNodeContinueExpanding(node, ASGSyntaxBindPatternNode(derivation, bindableNameNode, node.value, allowsRebind = False))

        selector = ASGLiteralSymbolNode(ASGNodeSyntaxExpansionDerivation(self, node), self.builder.topLevelIdentifier('Symbol'), ':=')
        return self.fromNodeContinueExpanding(node, ASGSyntaxMessageSendNode(derivation, store, selector, [node.value]))

    @asgPatternMatchingOnNodeKind(ASGSyntaxArrayElementReferenceAtNode)
    def expandSyntaxArrayElementReferenceAtNode(self, node: ASGSyntaxArrayElementReferenceAtNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        array = self(node.array)
        index, typechecked = self.analyzeSizeNode(node.index)

        decayedArrayType = array.getTypeInEnvironment(self.environment).asDecayedType()
        if not decayedArrayType.isArrayTypeNode():
            arrayError = self.makeErrorAtNode('Expected value with an array type for the subscript operator.', array)
            assert False

        self.emitBoundsSize(node, index, decayedArrayType.size)
        elementReferenceType = self.builder.forSyntaxExpansionBuild(self, node, ASGReferenceTypeNode, decayedArrayType.baseType)
        return self.builder.forSyntaxExpansionBuild(self, node, ASGArrayElementReferenceAtNode, elementReferenceType, array, index)

    @asgPatternMatchingOnNodeKind(ASGSyntaxBinaryExpressionSequenceNode)
    def expandSyntaxBinaryExpressionSequenceNode(self, node: ASGSyntaxBinaryExpressionSequenceNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)

        elementCount = len(node.elements)
        assert elementCount >= 1

        # TODO: Use an operator precedence parser
        previous = node.elements[0]
        i = 1
        derivation = ASGNodeSyntaxExpansionDerivation(self, node)
        while i < elementCount:
            operator = node.elements[i]
            operand = node.elements[i + 1]
            previous = ASGSyntaxMessageSendNode(derivation, previous, operator, [operand])
            i += 2

        return self.fromNodeContinueExpanding(node, previous)

    @asgPatternMatchingOnNodeKind(ASGSyntaxBindPatternNode)
    def expandSyntaxBindPatternNode(self, node: ASGSyntaxBindPatternNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        return self.fromNodeContinueExpanding(node, node.pattern.expandPatternWithValueAt(self, node.value, node))
    
    def decayAnalyzedValue(self, node: ASGNode):
        # TODO: Implement this properly
        return node

    @asgPatternMatchingOnNodeKind(ASGSyntaxBindingDefinitionNode)
    def expandSyntaxBindingDefinitionNode(self, node: ASGSyntaxBindingDefinitionNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        name = self.evaluateOptionalSymbol(node.nameExpression)
        expectedType = self.analyzeOptionalTypeExpression(node.typeExpression)
        value, typechecked = self.analyzeNodeWithExpectedType(node.valueExpression, expectedType)
        value = value.asASGDataNode()
        isMutable = node.isMutable
        if node.isMutable:
            decayedValueType = value.getTypeInEnvironment(self.environment).asDecayedType()
            referenceType = self.builder.forSyntaxExpansionBuild(self, node, ASGReferenceTypeNode, decayedValueType)
            alloca = self.builder.forSyntaxExpansionBuild(self, node, ASGAllocaNode, referenceType, decayedValueType)
            self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGStoreNode, alloca, value, predecessor = self.builder.currentPredecessor)
            value = alloca
        if name is None:
            return value

        self.environment = self.environment.childWithSymbolBinding(name, value)
        return value

    @asgPatternMatchingOnNodeKind(ASGSyntaxFunctionalDependentTypeNode)
    def expandSyntaxFunctionalDependentTypeNode(self, node: ASGSyntaxFunctionalDependentTypeNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)

        if node.argumentPattern is None:
            return self.fromNodeContinueExpanding(node, ASGSyntaxPiNode(ASGNodeSyntaxExpansionDerivation(self, node), [], node.resultType))

        argumentNodes, isExistential, isVariadic = node.argumentPattern.parseAndUnpackArgumentsPattern()
        if isExistential:
            return self.fromNodeContinueExpanding(node, ASGSyntaxSigmaNode(ASGNodeSyntaxExpansionDerivation(self, node), argumentNodes, node.resultType, isVariadic = isVariadic))
        else:
            return self.fromNodeContinueExpanding(node, ASGSyntaxPiNode(ASGNodeSyntaxExpansionDerivation(self, node), argumentNodes, node.resultType, isVariadic = isVariadic))

    @asgPatternMatchingOnNodeKind(ASGSyntaxFunctionNode)
    def expandSyntaxFunctionNode(self, node: ASGSyntaxFunctionNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        functionalType = self.expandMacrosOnly(node.functionalType)
        if not functionalType.isKindOf(ASGSyntaxFunctionalDependentTypeNode):
            return self.makeErrorAtNode(functionalType, 'Expected a functional dependent type.')
        
        return self.fromNodeContinueExpanding(node, functionalType.constructLambdaWithBody(ASGNodeSyntaxExpansionDerivation(self, node), node.nameExpression, node.body, node.isFixpoint))

    @asgPatternMatchingOnNodeKind(ASGSyntaxLambdaNode)
    def expandSyntaxLambdaNode(self, node: ASGSyntaxLambdaNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        functionalEnvironment = ASGFunctionalAnalysisEnvironment(self.environment, node.sourceDerivation.getSourcePosition())
        functionalAnalyzer = self.withFunctionalAnalysisEnvironment(functionalEnvironment)
        typedArguments = []
        arguments = node.arguments
        for i in range(len(arguments)):
            argument = arguments[i]
            typedArgument = self.analyzeArgumentNode(functionalAnalyzer, argument, i)
            if typedArgument.isKindOf(ASGArgumentNode):
                functionalEnvironment.addArgumentBinding(typedArgument)
                typedArguments.append(typedArgument)
        functionalAnalyzer.builder.currentPredecessor = None

        resultType = functionalAnalyzer.analyzeTypeExpression(node.resultType)
        name = self.evaluateOptionalSymbol(node.nameExpression)

        piType = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGPiNode, typedArguments, resultType, isVariadic = node.isVariadic, callingConvention = node.callingConvention)

        functionalAnalyzer.builder.currentPredecessor = None
        entryPoint = functionalAnalyzer.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGSequenceEntryNode)

        body, bodyTypechecked = functionalAnalyzer.analyzeNodeWithExpectedType(node.body, resultType)
        bodyReturn = functionalAnalyzer.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGSequenceReturnNode, body, predecessor = functionalAnalyzer.builder.currentPredecessor)
        
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLambdaNode, piType, typedArguments, entryPoint, exitPoint = bodyReturn, name = name, callingConvention = node.callingConvention)
    
    def expandTopLevelScript(self, node: ASGNode) -> ASGTopLevelScriptNode:
        entryPoint = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGSequenceEntryNode)
        scriptResult = self(node)
        exitPoint = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGSequenceReturnNode, scriptResult, predecessor = self.builder.currentPredecessor)
        resultType = scriptResult.getTypeInEnvironment(self.environment)
        return self.builder.forSyntaxExpansionBuild(self, node, ASGTopLevelScriptNode, resultType, entryPoint, exitPoint = exitPoint)

    @asgPatternMatchingOnNodeKind(ASGSyntaxPiNode)
    def expandSyntaxPiNode(self, node: ASGSyntaxPiNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        functionalEnvironment = ASGFunctionalAnalysisEnvironment(self.environment, node.sourceDerivation.getSourcePosition())
        functionalAnalyzer = self.withFunctionalAnalysisEnvironment(functionalEnvironment)
        typedArguments = []
        arguments = node.arguments
        for i in range(len(arguments)):
            argument = arguments[i]
            typedArgument = self.analyzeArgumentNode(functionalAnalyzer, argument, i)
            if typedArgument.isKindOf(ASGArgumentNode):
                functionalEnvironment.addArgumentBinding(typedArgument)
                typedArguments.append(typedArgument)
        functionalAnalyzer.builder.currentPredecessor = None

        resultType = functionalAnalyzer.analyzeTypeExpression(node.resultType)
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGPiNode, typedArguments, resultType, isVariadic = node.isVariadic, callingConvention = node.callingConvention)

    @asgPatternMatchingOnNodeKind(ASGSyntaxLexicalBlockNode)
    def expandSyntaxLexicalBlock(self, node: ASGSyntaxLexicalBlockNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        lexicalEnvironment = ASGLexicalEnvironment(self.environment, node.sourceDerivation.getSourcePosition())
        return self.withChildLexicalEnvironmentDo(lexicalEnvironment, lambda: self(node.body))
    
    @asgPatternMatchingOnNodeKind(ASGSyntaxLiteralIntegerNode)
    def expandSyntaxLiteralIntegerNode(self, node: ASGSyntaxLiteralIntegerNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        type = self.builder.topLevelIdentifier('Integer')
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralIntegerNode, type, node.value)

    @asgPatternMatchingOnNodeKind(ASGSyntaxLiteralSymbolNode)
    def expandSyntaxLiteralSymbolNode(self, node: ASGSyntaxLiteralSymbolNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        type = self.builder.topLevelIdentifier('Symbol')
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralSymbolNode, type, node.value)

    @asgPatternMatchingOnNodeKind(ASGSyntaxLiteralStringNode)
    def expandSyntaxLiteralStringNode(self, node: ASGSyntaxLiteralSymbolNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        type: ASGProductTypeNode = self.builder.topLevelIdentifier('String').asASGTypeNode()
        assert type.isProductTypeNode()

        data = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralStringDataNode, type.elements[0], node.value)
        size = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralIntegerNode, type.elements[0], len(node.value))
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGTupleNode, type, [data, size])

    @asgPatternMatchingOnNodeKind(ASGSyntaxIdentifierReferenceNode)
    def expandSyntaxIdentifierReferenceNode(self, node: ASGSyntaxIdentifierReferenceNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        lookupResults = self.environment.lookSymbolBindingListRecursively(node.value)
        if len(lookupResults) == 0:
            return self.makeErrorAtNode('Failed to finding binding for symbol %s.' % node.value, node)
        elif len(lookupResults) == 1 or not lookupResults[0].getTypeInEnvironment(self.environment).isFunctionalTypeNode():
            return self(lookupResults[0])
        else:
            # Select the first overloaded functionals.
            overloadedAlternatives = []
            overloadedAlternativeTypes = []
            for lookupResult in lookupResults:
                lookupResultType = lookupResult.getTypeInEnvironment(self.environment)
                if not lookupResultType.isFunctionalTypeNode():
                    break

                overloadedAlternatives.append(lookupResult)
                overloadedAlternativeTypes.append(lookupResultType)

            # If we only have one overloaded alternative, select it.
            assert len(overloadedAlternatives) >= 1
            if len(overloadedAlternatives) == 1:
                return self(overloadedAlternatives[0]) 
            
            ## Overloaded type and its alternatives.
            overloadedType = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGOverloadedTypeNode, overloadedAlternativeTypes)
            return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGOverloadedAlternativesNode, overloadedType, overloadedAlternatives)

    @asgPatternMatchingOnNodeKind(ASGSyntaxMessageSendNode, when = lambda n: n.receiver is None)
    def expandSyntaxMessageSendNodeWithoutReceiver(self, node: ASGSyntaxMessageSendNode) -> ASGTypecheckedNode:
        return self.expandFunctionalApplicationMessageSendNode(node)

    @asgPatternMatchingOnNodeKind(ASGSyntaxMessageSendNode, when = lambda n: n.receiver is not None)
    def expandSyntaxMessageSendNodeWithReceiver(self, node: ASGSyntaxMessageSendNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        receiver = self(node.receiver)
        receiverType = receiver.getTypeInEnvironment(self.environment)
        return receiverType.expandSyntaxMessageSendNode(self, node)
    
    def attemptToEvaluateMessageSendSelector(self, node: ASGSyntaxMessageSendNode) -> str:
        symbolType = self.builder.topLevelIdentifier('Symbol')
        analyzedSelector, typechecked = self.analyzeNodeWithExpectedType(node.selector, symbolType)
        if not typechecked:
            return None
        
        analyzedSelector = analyzedSelector.asASGDataNode()
        if analyzedSelector.isLiteralNode():
            return analyzedSelector.value
        else:
            return None

    def expandFunctionalApplicationMessageSendNode(self, node: ASGSyntaxMessageSendNode) -> ASGTypecheckedNode:
        selectorValue = self.evaluateSymbol(node.selector)
        if selectorValue is None:
            ## Analyze the the receiver and the arguments to discover more errors.
            if node.receiver is not None: self(node.receiver)
            for arg in node.arguments:
                self(arg)
            return self.makeErrorAtNode('Cannot expand message send node without constant selector.', node)

        selectorIdentifier = ASGSyntaxIdentifierReferenceNode(ASGNodeSyntaxExpansionDerivation(self, node), selectorValue)
        applicationArguments = []
        if node.receiver is not None:
            applicationArguments.append(node.receiver)
        applicationArguments += node.arguments
        
        application = ASGSyntaxApplicationNode(ASGNodeSyntaxExpansionDerivation(self, node), selectorIdentifier, applicationArguments)
        return self.fromNodeContinueExpanding(node, application)

    @asgPatternMatchingOnNodeKind(ASGSyntaxApplicationNode)
    def expandSyntaxApplicationNode(self, node: ASGSyntaxApplicationNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        functional = self(node.functional)
        functionalType = functional.getTypeInEnvironment(self.environment)
        return functionalType.expandSyntaxApplicationNode(self, node)
    
    def expandErrorApplicationWithType(self, node: ASGSyntaxApplicationNode, errorType: ASGBottomTypeNode):
        self.syntaxPredecessorOf(node)

        # Analyze the functional and the arguments.
        functional = self(node.functional)
        analyzedArguments = list(map(self, node.arguments))

        # Make an application node with the error.
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGApplicationNode, errorType, functional, analyzedArguments)

    def expandSingleProductTypeArguments(self, arguments: list[ASGNode], requiredAgumentCount: int, isVariadic: bool):
        if requiredAgumentCount <= 1 or len(arguments) != 1:
            return arguments

        singleArgument = arguments[0]
        if singleArgument.isSyntaxTupleNode():
            return singleArgument.elements
        return arguments

    def expandDependentApplicationWithType(self, node: ASGSyntaxApplicationNode, dependentType: ASGPiNode):
        self.syntaxPredecessorOf(node)

        substitutionAlgorithm = ASGBetaSubstitutionAlgorithm(ASGBetaSubstitutionContext(), self.builder)
        requiredArgumentCount = len(dependentType.arguments)
        expandedArguments = self.expandSingleProductTypeArguments(node.arguments, requiredArgumentCount, dependentType.isVariadic)
        availableArgumentCount = len(expandedArguments)

        # Analyze the functional.
        functional = self(node.functional)

        # Analyze the direct checkeable arguments.
        directCheckeableArgumentCount = min(requiredArgumentCount, availableArgumentCount)
        expectedType = None
        analyzedArguments = []
        for i in range(directCheckeableArgumentCount):
            argumentValue: ASGNode = expandedArguments[i]
            argumentSpecification: ASGArgumentNode = dependentType.arguments[i]
            expectedType = substitutionAlgorithm.expandNode(argumentSpecification.type)
            analyzedArgument, typechecked = self.analyzeNodeWithExpectedType(argumentValue, expectedType)
            analyzedArguments.append(analyzedArgument)
            substitutionAlgorithm.substitutionContext.setSubstitutionForNode(argumentSpecification, analyzedArgument)

        # Analyze the remaining arguments
        if not dependentType.isVariadic:
            expectedType = None
        
        for i in range(directCheckeableArgumentCount, availableArgumentCount):
            argumentValue: ASGNode = expandedArguments[i]
            analyzedArgument, typechecked = self.analyzeNodeWithExpectedType(argumentValue, expectedType)
            analyzedArguments.append(analyzedArgument)

        # Analyze the result type.
        resultType = substitutionAlgorithm.expandNode(dependentType.resultType)

        # Make the application node
        if dependentType.isPureFunctional():
            application = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGApplicationNode, resultType, functional, analyzedArguments)
        else:
            application = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGFxApplicationNode, resultType, functional, analyzedArguments, predecessor = self.builder.currentPredecessor)

        # Check the argument sizes.
        if requiredArgumentCount != availableArgumentCount:
            if not dependentType.isVariadic:
                return self.makeErrorAtNode('Application argument count mismatch. Got %d instead of %d arguments.' % (availableArgumentCount, requiredArgumentCount), node)
            elif availableArgumentCount < requiredArgumentCount - 1: 
                return self.makeErrorAtNode('Required at least %d arguments for variadic application.' % requiredArgumentCount, node)
        
        return application
    
    def expandFunctionApplicationWithType(self, node: ASGSyntaxApplicationNode, functionType: ASGFunctionTypeNode):
        self.syntaxPredecessorOf(node)

        requiredArgumentCount = len(functionType.arguments)
        expandedArguments = self.expandSingleProductTypeArguments(node.arguments, requiredArgumentCount, functionType.isVariadic)
        availableArgumentCount = len(expandedArguments)

        # Analyze the functional.
        functional = self(node.functional)

        # Analyze the direct checkeable arguments.
        directCheckeableArgumentCount = min(requiredArgumentCount, availableArgumentCount)
        expectedType: ASGNode = None
        analyzedArguments = []
        for i in range(directCheckeableArgumentCount):
            argumentValue: ASGNode = expandedArguments[i]
            expectedType = functionType.arguments[i]
            analyzedArgument, typechecked = self.analyzeNodeWithExpectedType(argumentValue, expectedType)
            if not typechecked and functionType.isVariadic:
                pass
            analyzedArguments.append(analyzedArgument)

        # Analyze the remaining arguments
        if not functionType.isVariadic:
            expectedType = None
        
        for i in range(directCheckeableArgumentCount, availableArgumentCount):
            argumentValue: ASGNode = expandedArguments[i]
            analyzedArgument, typechecked = self.analyzeNodeWithExpectedType(argumentValue, expectedType)
            analyzedArguments.append(analyzedArgument)

        # Retrieve the result type.
        resultType = functionType.resultType

        # Make the application node
        if functionType.isPureFunctional():
            application = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGApplicationNode, resultType, functional, analyzedArguments)
        else:
            application = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGFxApplicationNode, resultType, functional, analyzedArguments, predecessor = self.builder.currentPredecessor)

        # Check the argument sizes.
        if requiredArgumentCount != availableArgumentCount:
            if not functionType.isVariadic:
                return self.makeErrorAtNode('Application argument count mismatch. Got %d instead of %d arguments.' % (availableArgumentCount, requiredArgumentCount), node)
            elif availableArgumentCount < requiredArgumentCount: 
                return self.makeErrorAtNode('Required at least %d arguments for variadic application.' % requiredArgumentCount, node)
        
        return application
    
    def expandOverloadedApplicationWithType(self, node: ASGSyntaxApplicationNode, overloadedType: ASGOverloadedTypeNode):
        self.syntaxPredecessorOf(node)

        overloadedFunctional = self(node.functional)

        alternativesWithErrors = []

        for i in range(len(overloadedType.alternatives)):
            alternativeType = overloadedType.alternatives[i]
            functionalAlternative = self.builder.forSyntaxExpansionBuild(self, node, ASGOverloadedAlternativeSelectionNode, alternativeType, i, overloadedFunctional)
            functionalAlternative = self.reductionAlgorithm(functionalAlternative.asASGDataNode())

            alternativeApplicationNode = ASGSyntaxApplicationNode(ASGNodeSyntaxExpansionDerivation(self, node), functionalAlternative, node.arguments, kind = node.kind)
            alternativeExpandedResult, expansionTypecheckingErrors = self.attemptExpansionOfNode(alternativeApplicationNode)
            if len(expansionTypecheckingErrors) == 0:
                return alternativeExpandedResult
            
            alternativesWithErrors.append((functionalAlternative, expansionTypecheckingErrors))

        # Ensure the arguments are checked for generating the error messages.
        for argument in node.arguments:
            self(argument)

        # TODO: Properly format the error message.
        return self.makeErrorAtNode('Failed to find matching overloaded alternative.', node)
    
    def expandMacroApplicationWithType(self, node: ASGSyntaxApplicationNode, macroFunctionType: ASGMacroFunctionTypeNode):
        self.syntaxPredecessorOf(node)
        macro = self(node.functional)
        
        requiredArgumentCount = len(macroFunctionType.arguments)
        availableArgumentCount = len(node.arguments)
        # Check the argument sizes.
        if requiredArgumentCount != availableArgumentCount:
            if not macroFunctionType.isVariadic:
                return self.makeErrorAtNode('Macro application argument count mismatch. Got %d instead of %d arguments.' % (availableArgumentCount, requiredArgumentCount), node)
            elif availableArgumentCount < requiredArgumentCount: 
                return self.makeErrorAtNode('Required at least %d arguments for variadic macro application.' % requiredArgumentCount, node)
            
        # The macro must be a literal primitive or a lambda node.
        macroExpansionDerivation = ASGNodeMacroExpansionDerivation(self, node, macro)
        macroContext = ASGMacroContext(macroExpansionDerivation, self)
        if macro.isLiteralPrimitiveFunction():
            expanded = macro.compileTimeImplementation(macroContext, *node.arguments)
            return self.fromNodeContinueExpanding(node, expanded)
        elif macro.isLambda():
            assert False
        else:
            return self.makeErrorAtNode('Cannot expand a macro application without knowing the macro during compile time.', node)
        
    def analyzeBooleanCondition(self, node: ASGNode):
        return self.analyzeNodeWithExpectedType(node, self.builder.topLevelIdentifier('Boolean'))

    def analyzeSizeNode(self, node: ASGNode):
        return self.analyzeNodeWithExpectedType(node, self.builder.topLevelIdentifier('Size'))

    def analyzeDivergentBranchExpression(self, node: ASGNode) -> tuple[ASGSequenceEntryNode, ASGNode]:
        branchAnalyzer = self.withDivergingEnvironment(ASGLexicalEnvironment(self.environment, node.sourceDerivation.getSourcePosition()))
        entryPoint = branchAnalyzer.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGSequenceEntryNode)
        branchResult = branchAnalyzer(node)
        exitPoint = branchAnalyzer.builder.currentPredecessor
        return entryPoint, exitPoint, branchResult, branchAnalyzer

    def analyzeOptionalDivergentBranchExpression(self, divergenceNode: ASGNode, branchNode: ASGNode) -> tuple[ASGSequenceEntryNode, ASGNode]:
        expansionNode = branchNode
        if branchNode is None:
            expansionNode = divergenceNode        
        
        branchAnalyzer = self.withDivergingEnvironment(ASGLexicalEnvironment(self.environment, expansionNode.sourceDerivation.getSourcePosition()))
        entryPoint = branchAnalyzer.builder.forSyntaxExpansionBuildAndSequence(self, expansionNode, ASGSequenceEntryNode)
        if branchNode is not None:
            branchResult = branchAnalyzer(branchNode)
        else:
            branchResult = self.expandVoidConstantFor(expansionNode)
        exitPoint = branchAnalyzer.builder.currentPredecessor
        return entryPoint, exitPoint, branchResult, branchAnalyzer
        
    def mergeTypesOfBranches(self, branches: list[ASGNode]):
        if len(branches) == 0:
            return self.builder.topLevelIdentifier('Void')
        
        mergedBranchType = None
        for branch in branches:
            branchType = branch.getTypeInEnvironment(self.environment)
            if mergedBranchType is None:
                mergedBranchType = branchType
            elif not branchType.unificationEquals(mergedBranchType):
                return None
        return mergedBranchType

    @asgPatternMatchingOnNodeKind(ASGSyntaxIfThenElseNode)
    def expandSyntaxIfThenElseNode(self, node: ASGSyntaxIfThenElseNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        condition, typechecked = self.analyzeBooleanCondition(node.condition)
        trueEntryPoint, trueExitPoint, trueResult, trueBranchAnalyzer = self.analyzeOptionalDivergentBranchExpression(node, node.trueExpression)
        falseEntryPoint, falseExitPoint, falseResult, falseBranchAnalyzer = self.analyzeOptionalDivergentBranchExpression(node, node.falseExpression)
        branch = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGConditionalBranchNode, condition, trueEntryPoint, falseEntryPoint, predecessor = self.builder.currentPredecessor)

        trueExitPoint = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGSequenceBranchEndNode, predecessor = trueExitPoint, divergence = branch)
        falseExitPoint = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGSequenceBranchEndNode, predecessor = falseExitPoint, divergence = branch)

        mergedBranchType = self.mergeTypesOfBranches([trueResult, falseResult])
        branchResult = None
        convergenceValues = []
        phiIncomingValues = None

        # If failed to merge the branch result type, emit unit.
        if mergedBranchType is None:
            mergedBranchType = self.builder.topLevelIdentifier('Void')

        if not mergedBranchType.isUnitTypeNode():
            phiIncomingValues = [
                self.builder.forSyntaxExpansionBuild(self, node, ASGPhiValueNode, mergedBranchType, trueResult, predecessor = trueExitPoint),
                self.builder.forSyntaxExpansionBuild(self, node, ASGPhiValueNode, mergedBranchType, falseResult, predecessor = falseExitPoint),
            ]

        convergence = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGSequenceConvergenceNode, divergence = branch, predecessors = [trueExitPoint, falseExitPoint])
        if mergedBranchType.isUnitTypeNode():
            return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralUnitNode, mergedBranchType)
        else:
            return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGPhiNode, mergedBranchType, phiIncomingValues, predecessor = convergence)

    def analyzeOptionalLoopBodyExpression(self, loopNode: ASGNode, bodyNode: ASGNode) -> tuple[ASGSequenceEntryNode, ASGNode]:
        expansionNode = bodyNode
        if bodyNode is None:
            expansionNode = loopNode

        loopBodyEnvironment = ASGLoopBodyEnvironment(self.environment, expansionNode.sourceDerivation.getSourcePosition())
        bodyAnalyzer = self.withDivergingEnvironment(loopBodyEnvironment)
        entryPoint = bodyAnalyzer.builder.forSyntaxExpansionBuildAndSequence(self, expansionNode, ASGLoopBodyEntry)
        loopBodyEnvironment.loopBodyEntryNode = entryPoint

        if bodyNode is not None:
            bodyAnalyzer(bodyNode)

        exitPoint = bodyAnalyzer.builder.currentPredecessor
        if not exitPoint.isSequenceTerminatorNode():
            implicitContinue = bodyAnalyzer.builder.forSyntaxExpansionBuildAndSequence(self, expansionNode, ASGLoopContinueNode, exitPoint, entryPoint)
            bodyAnalyzer.environment.addContinueNodeToCurrentLoop(implicitContinue)
        return entryPoint, loopBodyEnvironment.breakNodes, loopBodyEnvironment.continueNodes

    def analyzeOptionalLoopContinueExpression(self, loopNode: ASGNode, loopBodyEntryNode: ASGNode, continueNodes: list[ASGNode], continueExpressionNode: ASGNode) -> tuple[ASGSequenceEntryNode, ASGNode]:
        expansionNode = continueExpressionNode
        if continueExpressionNode is None:
            expansionNode = loopNode

        continueAnalyzer = self.withDivergingEnvironment(ASGLexicalEnvironment(self.environment, expansionNode.sourceDerivation.getSourcePosition()))
        entryPoint = continueAnalyzer.builder.forSyntaxExpansionBuildAndSequence(self, expansionNode, ASGLoopContinueEntry, loopBodyEntryNode, continueNodes)
        if continueExpressionNode is not None:
            continueAnalyzer(continueExpressionNode)

        exitPoint = continueAnalyzer.builder.currentPredecessor
        return entryPoint, exitPoint

    def analyzeOptionalLoopConditionExpression(self, loopExpressionNode: ASGNode, loopNode: ASGNode, predecessor: ASGNode, conditionExpression: ASGNode) -> tuple[ASGSequenceEntryNode, ASGNode]:
        expansionNode = conditionExpression
        if conditionExpression is None:
            expansionNode = loopExpressionNode

        conditionAnalyzer = self.withDivergingEnvironment(ASGLexicalEnvironment(self.environment, expansionNode.sourceDerivation.getSourcePosition()))
        conditionAnalyzer.builder.currentPredecessor = predecessor
        conditionValue = None
        if conditionExpression is not None:
            conditionValue, typechecked = conditionAnalyzer.analyzeBooleanCondition(conditionExpression)

        return conditionAnalyzer.builder.forSyntaxExpansionBuildAndSequence(self, expansionNode, ASGLoopIterationEndNode, conditionValue, conditionAnalyzer.builder.currentPredecessor, loopNode)
    
    @asgPatternMatchingOnNodeKind(ASGSyntaxDoContinueWithWhileNode)
    def expandSyntaxDoContinueWithWhileNode(self, node: ASGSyntaxDoContinueWithWhileNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)

        loopBodyEntryNode, breakNodes, continueNodes = self.analyzeOptionalLoopBodyExpression(node, node.body)
        loopContinueEntryNode, continueExitNode = self.analyzeOptionalLoopContinueExpression(node, loopBodyEntryNode, continueNodes, node.continueExpression)

        loopNode = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLoopEntryNode, loopBodyEntryNode, loopContinueEntryNode, predecessor = self.builder.currentPredecessor)
        loopIterationEndNode = self.analyzeOptionalLoopConditionExpression(node, loopNode, continueExitNode, node.condition)

        self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGSequenceConvergenceNode, divergence = loopNode, predecessors = breakNodes + [loopIterationEndNode])
        return self.expandVoidConstantFor(node)

    @asgPatternMatchingOnNodeKind(ASGSyntaxWhileDoContinueWithNode)
    def expandSyntaxWhileDoContinueWith(self, node: ASGSyntaxWhileDoContinueWithNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        derivation = ASGNodeSyntaxExpansionDerivation(self, node)

        # Loop inversion. We perform loop inversion at this level to take advantage of Global Code Motion for loop invariant optimization.
        doWhileLoop = ASGSyntaxDoContinueWithWhileNode(derivation, node.body, node.continueExpression, node.condition)
        if node.condition is None:
            return self.fromNodeContinueExpanding(node, doWhileLoop)

        firstIterationCondition = ASGSyntaxIfThenElseNode(derivation, node.condition, doWhileLoop, None)
        return self.fromNodeContinueExpanding(node, firstIterationCondition)
    
    def expandVoidConstantFor(self, node: ASGNode) -> ASGTypecheckedNode:
        type = self.builder.topLevelIdentifier('Void')
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralUnitNode, type)

    @asgPatternMatchingOnNodeKind(ASGSyntaxSequenceNode)
    def expandSyntaxSequenceNode(self, node: ASGSyntaxSequenceNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        if len(node.elements) == 0:
            return self.expandVoidConstantFor(node)

        elementsToExpand = node.elements
        for i in range(len(elementsToExpand)):
            if i + 1 < len(elementsToExpand):
                self(elementsToExpand[i])
            else:
                return self.fromNodeContinueExpanding(node, elementsToExpand[i])
        assert False, "Should not reach here."
    
    @asgPatternMatchingOnNodeKind(ASGSyntaxTupleNode)
    def expandSyntaxTupleNode(self, node: ASGSyntaxTupleNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        if len(node.elements) == 0:
            type = self.builder.topLevelIdentifier('Void')
            return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGLiteralUnitNode, type)
        
        elements = []
        for element in node.elements:
            expandedElement = self(element)
            elements.append(expandedElement)

        # If there are all elements, then this is a product type formation node
        if all(element.isTypeNode() for element in elements):
            return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGProductTypeNode, elements)

        elementTypes = list(map(lambda n: n.asASGDataNode().getTypeInEnvironment(self.environment), elements))
        type = self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGProductTypeNode, elementTypes)
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGTupleNode, type, elements)

    @asgPatternMatchingOnNodeKind(ASGSyntaxExportName)
    def expandSyntaxExportNode(self, node: ASGSyntaxExportName) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        externalName = self.evaluateSymbol(node.externalName)
        exportedName = self.evaluateSymbol(node.exportedName)
        value = self(node.valueExpression)
        self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGExportNode, externalName, exportedName, value, predecessor = self.builder.currentPredecessor)
        return value

    @asgPatternMatchingOnNodeKind(ASGSyntaxFromExternalImportNode)
    def expandSyntaxFromExternalImportNode(self, node: ASGSyntaxFromExternalImportNode) -> ASGTypecheckedNode:
        self.syntaxPredecessorOf(node)
        externalName = self.evaluateSymbol(node.externalName)
        importedName = self.evaluateSymbol(node.importedName)
        type = self.analyzeTypeExpression(node.typeExpression)
        return self.builder.forSyntaxExpansionBuildAndSequence(self, node, ASGFromExternalImportNode, type, externalName, importedName)

    @asgPatternMatchingOnNodeKind(ASGTypecheckedNode)
    def expandSyntaxTypecheckedNode(self, node: ASGTypecheckedNode) -> ASGTypecheckedNode:
        return node

def expandAndTypecheck(environment: ASGEnvironment, node: ASGNode):
    expander = ASGExpandAndTypecheckingAlgorithm(environment)
    result = expander.expandTopLevelScript(node)
    return result, expander.errorAccumulator.errorList
