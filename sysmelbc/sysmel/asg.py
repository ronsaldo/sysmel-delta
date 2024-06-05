from .mop import *
from .syntax import *

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
    def isSequenceEntryNode(self) -> bool:
        return True

class ASGSequenceDivergenceNode(ASGSequencingNode):
    predecessor = ASGSequencingPredecessorAttribute()

class ASGConditionalBranchNode(ASGSequenceDivergenceNode):
    condition = ASGNodeDataInputPort()
    trueDestination = ASGSequencingDestinationPort()
    falseDestination = ASGSequencingDestinationPort()

class ASGSequenceConvergenceNode(ASGSequencingNode):
    divergence = ASGSequencingPredecessorAttribute()
    predecessors = ASGSequencingPredecessorsAttribute()
    values = ASGNodeDataInputPorts()

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

class ASGTypedDataExpressionNode(ASGTypedExpressionNode):
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

class ASGCapturedValueNode(ASGBetaReplaceableNode):
    pass

class ASGBaseTypeNode(ASGTypeNode):
    name = ASGNodeDataAttribute(str)

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
    pass

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
    def normalizeValue(self, value):
        intValue = int(value)
        bitSize = self.size * 8
        mask = (1 << bitSize) - 1
        return intValue & mask

    def makeLiteralWithValue(self, derivation, value: int):
        return ASGLiteralCharacterNode(derivation, self, self.normalizeValue(value))

class ASGPrimitiveIntegerTypeNode(ASGPrimitiveType):
    isSigned = ASGNodeDataAttribute(int)

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

    def isProductTypeNode(self) -> bool:
        return True

    def prettyPrintNameWithDataAttributes(self) -> str:
        if self.name is not None:
            return self.name
        return super().prettyPrintNameWithDataAttributes()

class ASGRecordTypeNode(ASGProductTypeNode):
    fieldNames = ASGNodeDataAttribute(tuple)

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
    arguments = ASGNodeDataInputPorts()
    entryPoint = ASGSequencingDestinationPort()
    result = ASGNodeDataInputPort()
    exitPoint = ASGSequencingPredecessorAttribute()
    callingConvention = ASGNodeDataAttribute(str, default = None)

    def isLambda(self) -> bool:
        return True

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

    def isLiteralAlwaysReducedPrimitiveApplication(self):
        return self.functional.isAlwaysReducedPrimitive()

class ASGInjectSum(ASGTypedDataExpressionNode):
    index = ASGNodeDataAttribute(int)
    value = ASGNodeDataInputPort()

class ASGTopLevelScriptNode(ASGTypedDataExpressionNode):
    entryPoint = ASGSequencingDestinationPort()
    result = ASGNodeDataInputPort()
    exitPoint = ASGSequencingPredecessorAttribute()

class ASGPhiValueNode(ASGTypedDataExpressionNode):
    value = ASGNodeDataInputPort()
    predecessor = ASGSequencingPredecessorAttribute()

class ASGPhiNode(ASGTypedDataExpressionNode):
    values = ASGNodeDataInputPorts()

class ASGSumTypeNode(ASGTypeNode):
    variants = ASGNodeTypeInputNodes()
    name = ASGNodeDataAttribute(str, default = None)

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

class ASGDecoratedTypeNode(ASGDerivedTypeNode):
    def mutableConstructorImpl(cls, derivation, baseType):
        # TODO: Implement properly
        return baseType

    def volatileConstructorImpl(cls, derivation, baseType):
        # TODO: Implement properly
        return baseType

class ASGArrayTypeNode(ASGDerivedTypeNode):
    size = ASGNodeDataInputPort()

    @classmethod
    def constructorImpl(cls, derivation, resultType, baseType, size):
        return cls(derivation, baseType, size)
    
class ASGPointerLikeTypeNode(ASGDerivedTypeNode):
    @classmethod
    def constructorImpl(cls, derivation, resultType, baseType):
        return cls(derivation, baseType)

class ASGPointerTypeNode(ASGPointerLikeTypeNode):
    pass

class ASGReferenceLikeTypeNode(ASGPointerLikeTypeNode):
    pass

class ASGReferenceTypeNode(ASGReferenceLikeTypeNode):
    pass

class ASGTemporaryReferenceTypeNode(ASGReferenceLikeTypeNode):
    pass

class ASGFromExternalImportNode(ASGTypedDataExpressionNode):
    externalName = ASGNodeDataAttribute(str)
    importedName = ASGNodeDataAttribute(str)
