from .mop import *
from .syntax import *
from .sdvmInstructions import *
from .memoryDescriptor import *
from .target import *
from .util import *

class ASGTypecheckedNode(ASGNode):
    sourceDerivation = ASGNodeSourceDerivationAttribute()

    def asASGNodeDerivation(self):
        return self.sourceDerivation

class ASGSequencingNode(ASGTypecheckedNode):
    def isPureDataNode(self) -> bool:
        return False

    def isSequencingNode(self) -> bool:
        return True
    
class ASGSequenceEntryNode(ASGSequencingNode):
    def isBasicBlockStart(self) -> bool:
        return True
    
    def isSequenceEntryNode(self) -> bool:
        return True
    
    def interpretInContext(self, context, parameterList):
        pass

class ASGSequenceDivergenceNode(ASGSequencingNode):
    predecessor = ASGSequencingPredecessorAttribute()

    def directImmediateDominator(self):
        return self.predecessor

class ASGConditionalBranchNode(ASGSequenceDivergenceNode):
    condition = ASGNodeDataInputPort()
    trueDestination = ASGSequencingDestinationPort()
    falseDestination = ASGSequencingDestinationPort()

    def getRegionOfUsedValue(self, usedValue):
        return self.predecessor

    def divergenceDestinations(self):
        yield self.trueDestination
        yield self.falseDestination

class ASGLoopEntryNode(ASGSequenceDivergenceNode):
    entryDestination = ASGSequencingDestinationPort()
    continueDestination = ASGSequencingDestinationPort()

    def divergenceDestinations(self):
        yield self.entryDestination
        yield self.continueDestination

    def immediateDivergenceDestinations(self):
        yield self.entryDestination

    def isLoopEntryNode(self):
        return True

class ASGLoopIterationEndNode(ASGSequencingNode):
    continueCondition = ASGNodeOptionalDataInputPort()
    predecessor = ASGSequencingPredecessorAttribute()
    loop = ASGSequencingPredecessorAttribute()

    def getRegionOfUsedValue(self, usedValue):
        return self.predecessor
    
    def isBasicBlockEnd(self) -> bool:
        return True

    def directImmediateDominator(self):
        return self.predecessor

class ASGLoopBodyEntry(ASGSequenceEntryNode):
    pass

class ASGLoopBreakNode(ASGSequencingNode):
    predecessor = ASGSequencingPredecessorAttribute()
    loopBodyEntry = ASGSequencingPredecessorAttribute()

    def isSequenceTerminatorNode(self) -> bool:
        return True

    def isLoopBreakNode(self) -> bool:
        return True

    def isBasicBlockEnd(self) -> bool:
        return True

    def directImmediateDominator(self):
        return self.predecessor

class ASGLoopContinueNode(ASGSequencingNode):
    predecessor = ASGSequencingPredecessorAttribute()
    loopBodyEntry = ASGSequencingPredecessorAttribute()

    def isSequenceTerminatorNode(self) -> bool:
        return True

    def isLoopEndNode(self) -> bool:
        return True

    def isBasicBlockEnd(self) -> bool:
        return True

    def directImmediateDominator(self):
        return self.predecessor

class ASGSequenceBranchEndNode(ASGSequencingNode):
    predecessor = ASGSequencingPredecessorAttribute()
    divergence = ASGSequencingPredecessorAttribute()

    def isBasicBlockEnd(self) -> bool:
        return True

    def directImmediateDominator(self):
        return self.predecessor
    
class ASGSequenceConvergenceNode(ASGSequencingNode):
    divergence = ASGSequencingPredecessorAttribute()
    predecessors = ASGSequencingPredecessorsAttribute()

    def isBasicBlockStart(self) -> bool:
        return True

    def isSequenceConvergenceNode(self) -> bool:
        return True

    def directImmediateDominator(self):
        if len(self.predecessors) == 1:
            return self.predecessors[0]
        return self.divergence

class ASGLoopContinueEntry(ASGSequenceConvergenceNode):
    pass

class ASGSequenceReturnNode(ASGSequencingNode):
    value = ASGNodeDataInputPort()
    predecessor = ASGSequencingPredecessorAttribute()

    def isSequenceTerminatorNode(self) -> bool:
        return True

    def isSequenceReturnNode(self) -> bool:
        return True

    def directImmediateDominator(self):
        return self.predecessor

    def getRegionOfUsedValue(self, usedValue):
        return self
    
    def interpretInContext(self, context, parameters):
        context.returnValue(context[parameters[0]])

class ASGTypedExpressionNode(ASGTypecheckedNode):
    type = ASGNodeTypeInputNode()

    def isTypeNode(self) -> bool:
        return self.type.isTypeUniverseNode()

    def getTypeInEnvironment(self, environment) -> ASGTypecheckedNode:
        return self.type

class ASGSequencingAndDataNode(ASGTypecheckedNode):
    predecessor = ASGSequencingPredecessorAttribute()
    type = ASGNodeTypeInputNode()

    def isPureDataNode(self) -> bool:
        return False

    def isSequencingNode(self) -> bool:
        return True

    def isTypeNode(self) -> bool:
        return self.type.isTypeUniverseNode()

    def getTypeInEnvironment(self, environment) -> ASGTypecheckedNode:
        return self.type

    def directImmediateDominator(self):
        return self.predecessor

class ASGMirSequencingAndDataNode(ASGSequencingAndDataNode):
    mirType = ASGNodeTypeInputNode()

class ASGTypedDataExpressionNode(ASGTypedExpressionNode):
    def isPureDataNode(self) -> bool:
        return True

class ASGTypedStatefullExpressionNode(ASGTypedExpressionNode):
    def isPureDataNode(self) -> bool:
        return False

    def isStatefullDataNode(self) -> bool:
        return True

class ASGMirTypedDataExpressionNode(ASGTypedExpressionNode):
    def isPureDataNode(self) -> bool:
        return True

class ASGErrorNode(ASGTypedDataExpressionNode):
    message = ASGNodeDataAttribute(str)
    innerNodes = ASGNodeDataInputPorts()

    def prettyPrintError(self) -> str:
        return '%s: %s' % (str(self.sourceDerivation.getSourcePosition()), self.message)

class ASGLiteralNode(ASGTypedDataExpressionNode):
    def isLiteralNode(self) -> bool:
        return True
    
    def isConstantDataNode(self) -> bool:
        return True
    
class ASGLiteralCharacterNode(ASGLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGLiteralIntegerNode(ASGLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGLiteralFloatNode(ASGLiteralNode):
    value = ASGNodeDataAttribute(float)

class ASGLiteralSymbolNode(ASGLiteralNode):
    value = ASGNodeDataAttribute(str)

class ASGLiteralStringDataNode(ASGLiteralNode):
    value = ASGNodeDataAttribute(str)
    nullTerminated = ASGNodeDataAttribute(bool, default = True)

class ASGLiteralUnitNode(ASGLiteralNode):
    pass

class ASGLiteralPrimitiveFunctionNode(ASGLiteralNode):
    name = ASGNodeDataAttribute(str)
    compileTimeImplementation = ASGNodeDataAttribute(object, default = None, notCompared = True, notPrinted = True)

    pure = ASGNodeDataAttribute(bool, default = False)
    compileTime = ASGNodeDataAttribute(bool, default = False)
    alwaysInline = ASGNodeDataAttribute(bool, default = False)

    def isLiteralPrimitiveFunction(self) -> bool:
        return True

    def isPureCompileTimePrimitive(self) -> bool:
        return self.pure and self.compileTime

    def isAlwaysReducedPrimitive(self) -> bool:
        return self.alwaysInline

    def reduceApplicationWithAlgorithm(self, node, algorithm):
        arguments = list(map(algorithm, node.arguments))
        return self.compileTimeImplementation(ASGNodeReductionDerivation(algorithm, node), node.type, *arguments)

class ASGTypeNode(ASGTypecheckedNode):
    def isTypeNode(self) -> bool:
        return True

    def isPureDataNode(self) -> bool:
        return True

    def getTypeUniverseIndex(self) -> int:
        return 0

    def getTypeInEnvironment(self, environment) -> ASGTypecheckedNode:
        return environment.getTopLevelTargetEnvironment().getTypeUniverseWithIndex(self.getTypeUniverseIndex())

class ASGBetaReplaceableNode(ASGTypedDataExpressionNode):
    def isBetaReplaceableNode(self) -> bool:
        return True

class ASGArgumentNode(ASGBetaReplaceableNode):
    index = ASGNodeDataAttribute(int, default = 0)
    name = ASGNodeDataAttribute(str, default = None, notCompared = True)
    isImplicit = ASGNodeDataAttribute(bool, default = False)

    def isArgumentNode(self) -> bool:
        return True

    def isActivationContextParameterDataNode(self):
        return True

class ASGCapturedValueNode(ASGBetaReplaceableNode):
    def isCapturedValueNode(self) -> bool:
        return True

    def isActivationContextParameterDataNode(self):
        return True

class ASGBaseTypeNode(ASGTypeNode):
    name = ASGNodeDataAttribute(str)

    def isConstantDataNode(self) -> bool:
        return True

    def normalizeValue(self, value):
        return value

    def prettyPrintNameWithDataAttributes(self):
        if self.name is not None:
            return self.name
        else:
            return super().prettyPrintNameWithDataAttributes()

class ASGSymbolTypeNode(ASGBaseTypeNode):
    pass

class ASGUnitTypeNode(ASGBaseTypeNode):
    def isUnitTypeNode(self) -> bool:
        return True

class ASGBottomTypeNode(ASGBaseTypeNode):
    def expandSyntaxApplicationNode(self, expander, applicationNode):
        return expander.expandErrorApplicationWithType(applicationNode, self)
    
    def isBottomTypeNode(self) -> bool:
        return True

class ASGIntegerTypeNode(ASGBaseTypeNode):
    def makeLiteralWithValue(self, derivation, value: int):
        return ASGLiteralIntegerNode(derivation, self, value)

class ASGPrimitiveType(ASGBaseTypeNode):
    size = ASGNodeDataAttribute(int)
    alignment = ASGNodeDataAttribute(int)

class ASGPrimitiveCharacterTypeNode(ASGPrimitiveType):
    def canBePassedAsCVarArgType(self) -> bool:
        return True

    def normalizeValue(self, value):
        intValue = int(value)
        bitSize = self.size * 8
        mask = (1 << bitSize) - 1
        return intValue & mask

    def makeLiteralWithValue(self, derivation, value: int):
        return ASGLiteralCharacterNode(derivation, self, self.normalizeValue(value))

class ASGPrimitiveIntegerTypeNode(ASGPrimitiveType):
    isSigned = ASGNodeDataAttribute(int)

    def canBePassedAsCVarArgType(self) -> bool:
        return True

    def normalizeValue(self, value):
        intValue = int(value)
        bitSize = self.size * 8
        if self.isSigned:
            signBit = 1 << (bitSize-1)
            return (intValue & (signBit - 1)) - (intValue & signBit)
        else:
            mask = (1 << bitSize) - 1
            return intValue & mask

    def makeLiteralWithValue(self, derivation, value: int):
        return ASGLiteralIntegerNode(derivation, self, self.normalizeValue(value))

class ASGPrimitiveFloatTypeNode(ASGPrimitiveType):
    def canBePassedAsCVarArgType(self) -> bool:
        return True

    def normalizeValue(self, value):
        floatValue = float(value)
        if self.size == 2:
            return struct.unpack('<e', struct.pack('<e', value))
        elif self.size == 4:
            return struct.unpack('<d', struct.pack('<d', value))
        else:
            return floatValue

    def makeLiteralWithValue(self, derivation, value: int):
        return ASGLiteralFloatNode(derivation, self, self.normalizeValue(value))

class ASGPrimitiveCVarArgTypeNode(ASGBaseTypeNode):
    def isSatisfiedAsTypeBy(self, otherType) -> bool:
        return otherType.canBePassedAsCVarArgType()

class ASGAnyTypeUniverseNode(ASGBaseTypeNode):
    def isTypeUniverseNode(self) -> bool:
        return True
    
    def isSatisfiedAsTypeBy(self, otherType) -> bool:
        if otherType.isTypeUniverseNode():
            return True

        return self.unificationEquals(otherType)

class ASGTypeUniverseNode(ASGTypeNode):
    index = ASGNodeDataAttribute(int)

    def isTypeUniverseNode(self) -> bool:
        return True

    def getTypeInEnvironment(self, environment) -> ASGTypecheckedNode:
        return environment.getTopLevelTargetEnvironment().getTypeUniverseWithIndex(self.index + 1)

    def expandSyntaxApplicationNode(self, expander, applicationNode: ASGSyntaxApplicationNode):
        return expander(applicationNode.functional).__class__.expandMetaSyntaxApplicationNode(expander, applicationNode)
    
class ASGProductTypeNode(ASGTypeNode):
    elements = ASGNodeTypeInputNodes()
    name = ASGNodeDataAttribute(str, default = None)

    def isConstructionTypeNode(self) -> bool:
        return True

    def isProductTypeNode(self) -> bool:
        return True

    def prettyPrintNameWithDataAttributes(self) -> str:
        if self.name is not None:
            return self.name
        return super().prettyPrintNameWithDataAttributes()

class ASGRecordTypeNode(ASGProductTypeNode):
    fieldNames = ASGNodeDataAttribute(tuple)

    def isConstructionTypeNode(self) -> bool:
        return True

    def isRecordTypeNode(self) -> bool:
        return True
    
    def expandSyntaxMessageSendNode(self, expander, messageSendNode):
        selector = expander.attemptToEvaluateMessageSendSelector(messageSendNode)
        if selector is not None:
            if len(messageSendNode.arguments) == 0:
                if selector in self.fieldNames:
                    fieldIndex = self.fieldNames.index(selector)
                    fieldType = self.elements[fieldIndex]
                    access = expander.builder.forSyntaxExpansionBuildAndSequence(expander, messageSendNode, ASGTupleAtNode, fieldType, expander(messageSendNode.receiver), fieldIndex)
                    return expander.fromNodeContinueExpanding(messageSendNode, access)
                    
        return super().expandSyntaxMessageSendNode(expander, messageSendNode)

class ASGStringTypeNode(ASGRecordTypeNode):
    def coerceExpressionIntoWith(self, expression, targetType, expander):
        if targetType.unificationEquals(self.elements[0]):
            elements = expander.builder.forSyntaxExpansionBuildAndSequence(expander, expression, ASGTupleAtNode, self.elements[0], expander(expression), 0)
            return expander.postProcessResult(elements)
        return expression

class ASGTupleNode(ASGTypedDataExpressionNode):
    elements = ASGNodeDataInputPorts()

    def isTupleNode(self) -> bool:
        return True

    def parseAndUnpackArgumentsPattern(self):
        isExistential = False
        isVariadic = False
        if len(self.elements) == 1 and self.elements[0].isBindableNameNode():
            isExistential = self.elements[0].isExistential
        if len(self.elements) > 0 and self.elements[-1].isBindableNameNode():
            isVariadic = self.elements[-1].isVariadic
        return self.elements, isExistential, isVariadic

class ASGTupleAtNode(ASGTypedDataExpressionNode):
    tuple = ASGNodeDataInputPort()
    index = ASGNodeDataAttribute(int)

class ASGMetaType(ASGBaseTypeNode):
    metaclass = ASGNodeDataAttribute(type, notPrinted = True)

class ASGLambdaNode(ASGTypedDataExpressionNode):
    arguments = ASGNodeDataInputPorts(notInterpreted = True)
    entryPoint = ASGSequencingDestinationPort(notInterpreted = True)
    exitPoint = ASGSequencingPredecessorAttribute(notInterpreted = True)
    name = ASGNodeDataAttribute(str, default = None, notCompared = True)
    callingConvention = ASGNodeDataAttribute(str, default = None)

    def scheduledDataDependencies(self):
        return ()

    def isConstantDataNode(self) -> bool:
        return self.type.isConstantDataNode()

    def isLambda(self) -> bool:
        return True

class ASGMirLambdaNode(ASGMirTypedDataExpressionNode):
    functionDefinition = ASGNodeDataInputPort()
    captures = ASGNodeDataInputPorts()
    name = ASGNodeDataAttribute(str, default = None)

    def isMirLambda(self) -> bool:
        return True

class ASGMirFunctionDefinitionNode(ASGMirTypedDataExpressionNode):
    arguments = ASGNodeDataInputPorts()
    entryPoint = ASGSequencingDestinationPort()
    exitPoint = ASGSequencingPredecessorAttribute()
    name = ASGNodeDataAttribute(str, default = None)
    callingConvention = ASGNodeDataAttribute(str, default = None)

    def isMirFunctionDefinition(self) -> bool:
        return True

class ASGMirPointerAddStridedIndex(ASGMirTypedDataExpressionNode):
    pointer = ASGNodeDataInputPort()
    stride = ASGNodeDataInputPort()
    index = ASGNodeDataInputPort()

class ASGMirPointerAddOffset(ASGMirTypedDataExpressionNode):
    pointer = ASGNodeDataInputPort()
    offset = ASGNodeDataInputPort()

class ASGApplicationNode(ASGTypedDataExpressionNode):
    functional = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()

    def isLiteralPureCompileTimePrimitiveApplication(self):
        return self.functional.isPureCompileTimePrimitive() and all(argument.isLiteralNode() for argument in self.arguments)

    def isLiteralAlwaysReducedPrimitiveApplication(self):
        return self.functional.isAlwaysReducedPrimitive()

class ASGFxApplicationNode(ASGSequencingAndDataNode):
    functional = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()
    
    def interpretInContext(self, context, parameters):
        functional = context[parameters[0]]
        arguments = list(map(lambda x: context[x], parameters[1:]))
        return functional(*arguments)

class ASGAllocaNode(ASGTypedStatefullExpressionNode):
    valueType = ASGNodeTypeInputNode(str)

class ASGLoadNode(ASGSequencingAndDataNode):
    pointer = ASGNodeDataInputPort()

    def getRegionOfUsedValue(self, usedValue):
        return self.predecessor

    def directImmediateDominator(self):
        return self.predecessor

class ASGBoundsCheckNode(ASGSequencingNode):
    index = ASGNodeDataInputPort()
    size = ASGNodeDataInputPort()
    predecessor = ASGSequencingPredecessorAttribute()

    def getRegionOfUsedValue(self, usedValue):
        return self.predecessor

    def directImmediateDominator(self):
        return self.predecessor
    
class ASGStoreNode(ASGSequencingNode):
    pointer = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()
    predecessor = ASGSequencingPredecessorAttribute()

    def getRegionOfUsedValue(self, usedValue):
        return self.predecessor

    def directImmediateDominator(self):
        return self.predecessor
    
class ASGInjectSum(ASGTypedDataExpressionNode):
    index = ASGNodeDataAttribute(int)
    value = ASGNodeDataInputPort()

    def isConstructionDataNode(self):
        return True
    
class ASGTopLevelScriptNode(ASGTypedDataExpressionNode):
    entryPoint = ASGSequencingDestinationPort()
    exitPoint = ASGSequencingPredecessorAttribute()

class ASGModuleTypeNode(ASGBaseTypeNode):
    pass

class ASGModuleNode(ASGTypedDataExpressionNode):
    topLevelScripts = ASGNodeDataInputPorts()
    exports = ASGNodeDataInputPorts()

class ASGPhiValueNode(ASGTypedDataExpressionNode):
    value = ASGNodeDataInputPort()
    predecessor = ASGSequencingPredecessorAttribute()

    def isPhiValueNode(self) -> bool:
        return True

class ASGPhiNode(ASGTypedDataExpressionNode):
    values = ASGNodeDataInputPorts()
    predecessor = ASGSequencingPredecessorAttribute()

    def isPhiNode(self) -> bool:
        return True

class ASGMirPhiNode(ASGTypedDataExpressionNode):
    values = ASGNodeDataInputPorts()

    def isPhiNode() -> bool:
        return True

class ASGSumTypeNode(ASGTypeNode):
    variants = ASGNodeTypeInputNodes()
    name = ASGNodeDataAttribute(str, default = None)

    def isConstructionTypeNode(self) -> bool:
        return True

    def makeBooleanWithValue(self, derivation, value: bool):
        if not value:
            return ASGInjectSum(derivation, self, 0, ASGLiteralUnitNode(derivation, self.variants[0]))
        else:
            return ASGInjectSum(derivation, self, 1, ASGLiteralUnitNode(derivation, self.variants[1]))

    def coerceExpressionWith(self, expression, expander):
        expressionType = expression.getTypeInEnvironment(expander.environment)
        if expressionType.isBottomTypeNode():
            return expression
        elif expressionType is not self:
            for i in range(len(self.variants)):
                variant = self.variants[i]
                if variant.isSatisfiedAsTypeBy(expressionType):
                    return expander.builder.forCoercionExpansionBuildAndSequence(expander, expression, ASGInjectSum, self, i, expression)

        return super().coerceExpressionWith(expression, expander)
    
    def prettyPrintNameWithDataAttributes(self) -> str:
        if self.name is not None:
            return self.name
        return super().prettyPrintNameWithDataAttributes()

class ASGOverloadedTypeNode(ASGTypeNode):
    alternatives = ASGNodeTypeInputNodes()

    def isConstructionTypeNode(self) -> bool:
        return True

    def expandSyntaxApplicationNode(self, expander, applicationNode):
        return expander.expandOverloadedApplicationWithType(applicationNode, self)
    
class ASGOverloadedAlternativesNode(ASGTypedDataExpressionNode):
    alternatives = ASGNodeDataInputPorts()

    def isOverloadedAlternativesNode(self) -> bool:
        return True

class ASGOverloadedAlternativeSelectionNode(ASGTypedDataExpressionNode):
    index = ASGNodeDataAttribute(int)
    alternatives = ASGNodeDataInputPort()

class ASGSigmaNode(ASGTypeNode):
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeDataInputPort()

class ASGPiNode(ASGTypeNode):
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeDataInputPort()
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    callingConvention = ASGNodeDataAttribute(str, default = None)

    ## TODO: Remove this when supporting dependent effects.
    pure = ASGNodeDataAttribute(bool, default = False)

    def isConstantDataNode(self) -> bool:
        # TODO: Return false if we have captures
        return True

    def isFunctionalTypeNode(self) -> bool:
        return True

    def isPureFunctional(self) -> bool:
        return self.pure

    def expandSyntaxApplicationNode(self, expander, applicationNode):
        return expander.expandDependentApplicationWithType(applicationNode, self)

class ASGFunctionTypeNode(ASGTypeNode):
    arguments = ASGNodeTypeInputNodes()
    resultType = ASGNodeTypeInputNode()
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    callingConvention = ASGNodeDataAttribute(str, default = None)
    pure = ASGNodeDataAttribute(bool, default = False)

    def isConstructionTypeNode(self) -> bool:
        return True

    def isFunctionalTypeNode(self) -> bool:
        return True

    def isPureFunctional(self) -> bool:
        return self.pure

    def expandSyntaxApplicationNode(self, expander, applicationNode):
        return expander.expandFunctionApplicationWithType(applicationNode, self)

class ASGMacroFunctionTypeNode(ASGTypeNode):
    arguments = ASGNodeTypeInputNodes()
    resultType = ASGNodeTypeInputNode()
    isVariadic = ASGNodeDataAttribute(bool, default = False)

    def isFunctionalTypeNode(self) -> bool:
        return True

    def expandSyntaxApplicationNode(self, expander, applicationNode):
        return expander.expandMacroApplicationWithType(applicationNode, self)

class ASGDerivedTypeNode(ASGTypeNode):
    baseType = ASGNodeTypeInputNode()

    def isConstructionTypeNode(self):
        return True

class ASGDecoratedTypeNode(ASGDerivedTypeNode):
    def mutableConstructorImpl(cls, derivation, baseType):
        # TODO: Implement properly
        return baseType

    def volatileConstructorImpl(cls, derivation, baseType):
        # TODO: Implement properly
        return baseType

    def asUndecoratedType(self):
        return self.baseType
    
    def computeIndexedElementOffsetAndStride(self, expander, node, index: ASGNode):
        return self.baseType.computeIndexedElementOffsetAndStride(expander, node, index)

class ASGArrayTypeNode(ASGDerivedTypeNode):
    size = ASGNodeDataInputPort()

    def isArrayTypeNode(self) -> bool:
        return True

    @classmethod
    def constructorImpl(cls, derivation, resultType, baseType, size):
        return cls(derivation, baseType, size)

    def expandSyntaxApplicationNode(self, expander, applicationNode):
        if applicationNode.isBracketKind() and len(applicationNode.arguments) == 1:
            return expander.fromNodeContinueExpanding(applicationNode, ASGSyntaxArrayElementReferenceAtNode(ASGNodeSyntaxExpansionDerivation(expander, applicationNode), applicationNode.functional, applicationNode.arguments[0]))
        return super().expandSyntaxApplicationNode(expander, applicationNode)

class ASGArrayElementAtNode(ASGTypedDataExpressionNode):
    array = ASGNodeDataInputPort()
    index = ASGNodeDataInputPort()

class ASGArrayElementReferenceAtNode(ASGTypedDataExpressionNode):
    array = ASGNodeDataInputPort()
    index = ASGNodeDataInputPort()

class ASGPointerLikeTypeNode(ASGDerivedTypeNode):
    @classmethod
    def constructorImpl(cls, derivation, resultType, baseType):
        return cls(derivation, baseType)

class ASGPointerTypeNode(ASGPointerLikeTypeNode):
    def canBePassedAsCVarArgType(self) -> bool:
        return True

class ASGReferenceLikeTypeNode(ASGPointerLikeTypeNode):
    def coerceExpressionIntoWith(self, expression, targetType, expander):
        if not targetType.asUndecoratedType().isReferenceLikeType():
            expandedExpression = expander(expression)
            loadedValue = expander.builder.forSyntaxExpansionBuildAndSequence(expander, expression, ASGLoadNode, self.baseType, expandedExpression, predecessor = expander.builder.currentPredecessor)
            loadedValue = expander.postProcessResult(loadedValue)
            return targetType.coerceExpressionWith(loadedValue, expander)

        return super().coerceExpressionIntoWith(expression, targetType, expander)

    def asDecayedType(self):
        return self.baseType.asUndecoratedType()
    
    def isReferenceLikeType(self) -> bool:
        return True

    def expandSyntaxMessageSendNode(self, expander, messageSendNode):
        selector = expander.attemptToEvaluateMessageSendSelector(messageSendNode)
        if selector is not None:
            if selector == ':=' and len(messageSendNode.arguments) == 1:
                ## TODO: Ensure that this is mutable reference.
                expectedValueType = self.baseType.asUndecoratedType()
                reference = expander(messageSendNode.receiver)
                coercedValued, typechecked = expander.analyzeNodeWithExpectedType(messageSendNode.arguments[0], expectedValueType)
                expander.builder.forSyntaxExpansionBuildAndSequence(expander, messageSendNode, ASGStoreNode, reference, coercedValued, predecessor = expander.builder.currentPredecessor)
                return reference
                    
        return super().expandSyntaxMessageSendNode(expander, messageSendNode)

class ASGReferenceTypeNode(ASGReferenceLikeTypeNode):
    pass

class ASGTemporaryReferenceTypeNode(ASGReferenceLikeTypeNode):
    pass

class ASGExportNode(ASGSequencingNode):
    externalName = ASGNodeDataAttribute(str)
    exportedName = ASGNodeDataAttribute(str)
    value = ASGNodeDataInputPort()
    predecessor = ASGSequencingPredecessorAttribute()

    def directImmediateDominator(self):
        return self.predecessor

    def isExportNode(self) -> bool:
        return True

    def interpretInContext(self, context, parameters):
        value = context[parameters[0]]
        context.getActiveModule().exportValueWithName(value, self.exportedName, externalName = self.externalName)

class ASGFromExternalImportNode(ASGTypedDataExpressionNode):
    externalName = ASGNodeDataAttribute(str)
    importedName = ASGNodeDataAttribute(str)

    def isConstantDataNode(self) -> bool:
        return True
    
class ASGMirFromExternalImportNode(ASGMirTypedDataExpressionNode):
    externalName = ASGNodeDataAttribute(str)
    importedName = ASGNodeDataAttribute(str)

    def isConstantDataNode(self) -> bool:
        return True

class ASGMirTypeNode(ASGTypeNode):
    def __init__(self, *positionalArguments, **kwArguments) -> None:
        super().__init__(*positionalArguments, **kwArguments)
        self.memoryDescriptor = None

    def getTypeInEnvironment(self, environment) -> ASGTypecheckedNode:
        return environment.getTopLevelTargetEnvironment().getMirTypeUniverse()
    
    def getSDVMArgumentInstructionWith(self, moduleFrontend):
        return moduleFrontend.argumentInstructionDictionary[self]

    def getSDVMLoadInstructionWith(self, moduleFrontend):
        return moduleFrontend.loadInstructionDictionary[self]

    def getSDVMLoadGCInstructionWith(self, moduleFrontend):
        return moduleFrontend.loadGCInstructionDictionary[self]

    def getSDVMStoreInstructionWith(self, moduleFrontend):
        return moduleFrontend.storeInstructionDictionary[self]

    def getSDVMStoreGCInstructionWith(self, moduleFrontend):
        return moduleFrontend.storeGCInstructionDictionary[self]

    def getSDVMCallArgumentInstructionWith(self, moduleFrontend):
        return moduleFrontend.callArgumentInstructionDictionary[self]

    def getSDVMCallClosureInstructionWith(self, moduleFrontend):
        return moduleFrontend.callClosureInstructionDictionary[self]

    def getSDVMCallInstructionWith(self, moduleFrontend):
        return moduleFrontend.callInstructionDictionary[self]

    def getSDVMReturnInstructionWith(self, moduleFrontend):
        return moduleFrontend.returnInstructionDictionary[self]
    
    def getMemoryDescriptor(self):
        if self.memoryDescriptor is None:
            self.memoryDescriptor = self.buildMemoryDescriptor()
        return self.memoryDescriptor
    
    def getAlignedSizeWithExpander(self, expander, node):
        alignedSize = self.getAlignedSize()
        return expander.makeLiteralSizeAt(node, alignedSize)

    def getAlignedSize(self) -> int:
        return alignedTo(self.getSize(), self.getAlignment())

    def getAlignment(self) -> int:
        raise Exception("Type with unknown alignment")

    def getSize(self) -> int:
        raise Exception("Type with unknown size")

    def buildMemoryDescriptor(self):
        return MemoryDescriptor(self.getSize(), self.getAlignment())

class ASGMirBaseTypeNode(ASGMirTypeNode):
    name = ASGNodeDataAttribute(str)
    size = ASGNodeDataAttribute(int)
    alignment = ASGNodeDataAttribute(int)

    def getSize(self) -> int:
        return self.size

    def getAlignment(self) -> int:
        return self.alignment

    def isConstantDataNode(self) -> bool:
        return True

    def normalizeValue(self, value):
        return value

    def prettyPrintNameWithDataAttributes(self):
        if self.name is not None:
            return self.name
        else:
            return super().prettyPrintNameWithDataAttributes()

class ASGMirCVarArgTypeNode(ASGMirBaseTypeNode):
    pass

class ASGMirFunctionTypeNode(ASGMirTypeNode):
    arguments = ASGNodeTypeInputNodes()
    resultType = ASGNodeTypeInputNode()
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    callingConvention = ASGNodeDataAttribute(str, default = None)
    pure = ASGNodeDataAttribute(bool, default = False)

    def isMirFunctionType(self) -> bool:
        return True
    
    def asFunctionType(self) -> bool:
        return self

    def getFixedArgumentCount(self) -> int:
        if self.isVariadic and len(self.arguments) > 0:
            return len(self.arguments) - 1
        else:
            return len(self.arguments)

class ASGMirClosureTypeNode(ASGMirTypeNode):
    functionType = ASGNodeTypeInputNode()

    def isMirClosureType(self) -> bool:
        return True
    
    def asTopLevelMirType(self) -> bool:
        return self.functionType

    def asFunctionType(self) -> bool:
        return self.functionType

class ASGMirDerivedTypeNode(ASGMirTypeNode):
    baseType = ASGNodeTypeInputNode()
    
class ASGMirArrayTypeNode(ASGMirDerivedTypeNode):
    size = ASGNodeDataInputPort()
    
    def isMirArrayType(self):
        return True

class ASGMirPointerTypeNode(ASGMirDerivedTypeNode):
    target = ASGNodeDataAttribute(CompilationTarget, notPrinted = True)

    def isMirPointerType(self):
        return True

    def getSDVMArgumentInstructionWith(self, moduleFrontend):
        return SdvmInstArgPointer

    def getSDVMCallArgumentInstructionWith(self, moduleFrontend):
        return SdvmInstCallArgPointer

    def getSDVMCallClosureInstructionWith(self, moduleFrontend):
        return SdvmInstCallClosurePointer

    def getSDVMCallInstructionWith(self, moduleFrontend):
        return SdvmInstCallPointer

    def getSDVMReturnInstructionWith(self, moduleFrontend):
        return SdvmInstReturnPointer

    def asFunctionType(self) -> bool:
        return self.baseType.asFunctionType()

    def getAlignment(self) -> int:
        return self.target.pointerAlignment

    def getSize(self) -> int:
        return self.target.pointerSize

    def computeIndexedElementOffsetAndStride(self, expander, node, index: ASGNode):
        return self.baseType, None, self.baseType.getAlignedSizeWithExpander(expander, node)

class ASGMirGCPointerTypeNode(ASGMirDerivedTypeNode):
    target = ASGNodeDataAttribute(CompilationTarget, notPrinted = True)

    def isMirGCPointerType(self):
        return True

    def getSDVMArgumentInstructionWith(self, moduleFrontend):
        return SdvmInstArgGCPointer

    def getSDVMCallArgumentInstructionWith(self, moduleFrontend):
        return SdvmInstCallArgGCPointer

    def getSDVMCallClosureInstructionWith(self, moduleFrontend):
        return SdvmInstCallClosureGCPointer

    def getSDVMCallInstructionWith(self, moduleFrontend):
        return SdvmInstCallGCPointer

    def getSDVMReturnInstructionWith(self, moduleFrontend):
        return SdvmInstReturnGCPointer

    def getAlignment(self) -> int:
        return self.target.gcPointerAlignment

    def getSize(self) -> int:
        return self.target.gcPointerSize

    def computeIndexedElementOffsetAndStride(self, expander, node, index: ASGNode):
        return self.baseType, None, self.baseType.getAlignedSizeWithExpander(expander, node)
    
class ASGMirVoidTypeNode(ASGMirBaseTypeNode):
    pass

class ASGMirTypeUniverseNode(ASGMirBaseTypeNode):
    def getSDVMArgumentInstructionWith(self, moduleFrontend):
        return SdvmInstArgGCPointer

    def getSDVMCallArgumentInstructionWith(self, moduleFrontend):
        return SdvmInstCallArgGCPointer

    def getSDVMCallClosureInstructionWith(self, moduleFrontend):
        return SdvmInstCallClosureGCPointer

    def getSDVMCallInstructionWith(self, moduleFrontend):
        return SdvmInstCallGCPointer

    def getSDVMReturnInstructionWith(self, moduleFrontend):
        return SdvmInstReturnGCPointer
