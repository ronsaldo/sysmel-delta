from .mop import *
from .environment import *
from .asg import *

class ASGNodeMirExpansionDerivation(ASGNodeExpansionDerivation):
    pass

class ASGMirReductionAlgorithm(ASGDynamicProgrammingReductionAlgorithm):
    def __init__(self) -> None:
        super().__init__()

class ASGMirTypeExpansionAlgorithm(ASGDynamicProgrammingAlgorithm):
    def __init__(self, builder: ASGBuilderWithGVNAndEnvironment) -> None:
        super().__init__()
        self.builder = builder
        for typeName, mirTypeName in [
            ('Void', 'MIR::Void'),
            ('Boolean', 'MIR::Boolean'),
            ('Int8',  'MIR::Int8'),
            ('Int16', 'MIR::Int16'),
            ('Int32', 'MIR::Int32'),
            ('Int64', 'MIR::Int64'),
            ('UInt8',  'MIR::UInt8'),
            ('UInt16', 'MIR::UInt16'),
            ('UInt32', 'MIR::UInt32'),
            ('UInt64', 'MIR::UInt64'),
            ('Float32', 'MIR::Float32'),
            ('Float64', 'MIR::Float64'),
        ]:
            type = self.builder.topLevelIdentifier(typeName)
            mirType = self.builder.topLevelIdentifier(mirTypeName)
            self.setValueForNodeExpansion(type, mirType)

    @asgPatternMatchingOnNodeKind(ASGPointerLikeTypeNode)
    def expandPointerLikeTypeNode(self, node: ASGPointerLikeTypeNode) -> ASGNode:
        baseType = self.expandNode(node.baseType)
        return self.builder.forMirTypeExpansionBuild(self, node, ASGMirPointerTypeNode, baseType)

    @asgPatternMatchingOnNodeKind(ASGArrayTypeNode)
    def expandArrayTypeNode(self, node: ASGArrayTypeNode) -> ASGNode:
        baseType = self.expandNode(node.baseType)

        if not node.size.isLiteralNode():
            return self.builder.forMirTypeExpansionBuild(self, node, ASGMirPointerTypeNode, baseType)
        
        if baseType.unificationEquals(node.baseType):
            return node

        return self.builder.forMirTypeExpansionBuild(self, node, ASGMirArrayTypeNode, baseType, node.size)

    @asgPatternMatchingOnNodeKind(ASGPiNode)
    def expandPiNode(self, node: ASGPiNode) -> ASGNode:
        resultType = self.expandNode(node.resultType)

        argumentTypes = []
        for argument in node.arguments:
            assert argument.isArgumentNode()
            self.expandNode(argument.type).appendInFlattenedList(argumentTypes)

        functionType = self.builder.forMirTypeExpansionBuild(self, node, ASGMirFunctionTypeNode, argumentTypes, resultType, isVariadic = node.isVariadic, callingConvention = node.callingConvention, pure = node.pure)
        return self.builder.forMirTypeExpansionBuild(self, node, ASGMirClosureTypeNode, functionType)

    @asgPatternMatchingOnNodeKind(ASGFunctionTypeNode)
    def expandFunctionTypeNode(self, node: ASGFunctionTypeNode) -> ASGNode:
        arguments = list(map(self.expandNode, node.arguments))
        resultType = self.expandNode(node.resultType)
        functionType = self.builder.forMirTypeExpansionBuild(self, node, ASGMirFunctionTypeNode, arguments, resultType, isVariadic = node.isVariadic, callingConvention = node.callingConvention, pure = node.pure)
        return self.builder.forMirTypeExpansionBuild(self, node, ASGMirClosureTypeNode, functionType)
    
    def expandNode(self, node: ASGNode) -> ASGNode:
        return node

    def expandFlattenedNodes(self, nodes: list[ASGNode]):
        expandedNodes = []
        for node in nodes:
            expandedNode = self.expandNode(node)
            expandedNode.appendInFlattenedList(expandedNodes)
        return expandedNodes
    
class ASGMirExpanderAlgorithm(ASGDynamicProgrammingAlgorithm):
    def __init__(self, target, builder: ASGBuilderWithGVN = None, reducer: ASGMirReductionAlgorithm = None, typeExpander: ASGMirTypeExpansionAlgorithm = None) -> None:
        super().__init__()
        self.target = target
        self.reducer = reducer
        self.builder = builder
        self.typeExpander = typeExpander
        self.moduleExports = []
        if self.builder is None:
            self.builder = ASGBuilderWithGVNAndEnvironment(None, ASGTopLevelTargetEnvironment.getForTarget(target))
        if self.reducer is None:
            self.reducer = ASGMirReductionAlgorithm()
        if self.typeExpander is None:
            self.typeExpander = ASGMirTypeExpansionAlgorithm(self.builder)

    def forChildEnvironment(self):
        return ASGMirExpanderAlgorithm(self.target, ASGBuilderWithGVNAndEnvironment(self.builder, self.builder.topLevelEnvironment), self.reducer, self.typeExpander)
    
    def expandMirType(self, type: ASGNode):
        return self.typeExpander(type)

    @asgPatternMatchingOnNodeKind(ASGLiteralCharacterNode)
    def expandLiteralCharacterNode(self, node: ASGLiteralCharacterNode) -> ASGNode:
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLiteralIntegerNode, self.expandMirType(node.type), node.value)

    @asgPatternMatchingOnNodeKind(ASGLiteralIntegerNode)
    def expandLiteralIntegerNode(self, node: ASGLiteralIntegerNode) -> ASGNode:
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLiteralIntegerNode, self.expandMirType(node.type), node.value)

    @asgPatternMatchingOnNodeKind(ASGLiteralFloatNode)
    def expandLiteralFloatNode(self, node: ASGLiteralFloatNode) -> ASGNode:
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLiteralFloatNode, self.expandMirType(node.type), node.value)

    @asgPatternMatchingOnNodeKind(ASGLiteralStringDataNode)
    def expandLiteralStringDataNode(self, node: ASGLiteralStringDataNode) -> ASGNode:
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLiteralStringDataNode, self.expandMirType(node.type), node.value)

    @asgPatternMatchingOnNodeKind(ASGLiteralPrimitiveFunctionNode)
    def expandLiteralPrimitiveFunctionNode(self, node: ASGLiteralPrimitiveFunctionNode) -> ASGNode:
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLiteralPrimitiveFunctionNode, self.expandMirType(node.type).asTopLevelMirType(), node.name, node.compileTimeImplementation, pure = node.pure, compileTime = node.compileTime, alwaysInline = node.alwaysInline)

    @asgPatternMatchingOnNodeKind(ASGTopLevelScriptNode)
    def expandSyntaxFromTopLevelScriptNode(self, node: ASGTopLevelScriptNode) -> ASGNode:
        type = self.expandNode(node.type)
        entryPoint = self.expandNode(node.entryPoint)
        exitPoint = self.expandNode(node.exitPoint)

        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGTopLevelScriptNode, type, entryPoint, exitPoint)

    @asgPatternMatchingOnNodeKind(ASGFromExternalImportNode)
    def expandFromExternalImportNode(self, node: ASGFromExternalImportNode) -> ASGNode:
        mirType = self.expandMirType(node.type).asTopLevelMirType()
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGMirFromExternalImportNode, mirType, node.externalName, node.importedName)
    
    @asgPatternMatchingOnNodeKind(ASGExportNode)
    def expandExportNode(self, node: ASGExportNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        value = self.expandNode(node.value)
        exportNode = self.builder.forMirExpansionBuildAndSequence(self, node, ASGExportNode, node.externalName, node.exportedName, value, predecessor = predecessor)
        self.moduleExports.append(exportNode)
        return exportNode

    @asgPatternMatchingOnNodeKind(ASGArgumentNode)
    def expandArgumentNode(self, node: ASGArgumentNode) -> ASGNode:
        mirType = self.expandMirType(node.type)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGArgumentNode, mirType, node.index, node.name, node.isImplicit)

    @asgPatternMatchingOnNodeKind(ASGApplicationNode)
    def expandApplicationNode(self, node: ASGApplicationNode) -> ASGNode:
        mirType = self.expandMirType(node.type)
        functional = self.expandNode(node.functional)
        arguments = self.expandFlattenedNodes(node.arguments)

        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGApplicationNode, mirType, functional, arguments)

    @asgPatternMatchingOnNodeKind(ASGFxApplicationNode)
    def expandFxApplicationNode(self, node: ASGFxApplicationNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        mirType = self.expandMirType(node.type)
        functional = self.expandNode(node.functional)
        arguments = self.expandFlattenedNodes(node.arguments)

        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGFxApplicationNode, mirType, functional, arguments, predecessor = predecessor)

    @asgPatternMatchingOnNodeKind(ASGPhiValueNode)
    def expandPhiValueNode(self, node: ASGPhiValueNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        mirType = self.expandMirType(node.type)
        value = self.expandNode(node.value)

        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGPhiValueNode, mirType, value, predecessor = predecessor)

    @asgPatternMatchingOnNodeKind(ASGPhiNode)
    def expandPhiNode(self, node: ASGPhiNode) -> ASGNode:
        mirType = self.expandMirType(node.type)
        values = self.expandNodes(node.values)

        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGPhiNode, mirType, values)

    @asgPatternMatchingOnNodeKind(ASGLambdaNode)
    def expandLambda(self, node: ASGLambdaNode) -> ASGNode:
        definitionExpander = self.forChildEnvironment()

        mirType = self.expandMirType(node.type)
        arguments = definitionExpander.expandFlattenedNodes(node.arguments)
        entryPoint = definitionExpander.expandNode(node.entryPoint)
        exitPoint = definitionExpander.expandNode(node.exitPoint)

        definition = self.builder.forMirExpansionBuildAndSequence(self, node, ASGMirFunctionDefinitionNode, mirType.functionType, arguments, entryPoint, node.callingConvention, name = node.name, exitPoint = exitPoint)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGMirLambdaNode, mirType, definition, [], name = node.name)

    @asgPatternMatchingOnNodeKind(ASGSequenceEntryNode)
    def expandSequenceEntryNode(self, node: ASGSequenceEntryNode) -> ASGNode:
        return node

    @asgPatternMatchingOnNodeKind(ASGConditionalBranchNode)
    def expandConditionalBranchNode(self, node: ASGConditionalBranchNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        condition = self.expandNode(node.condition)
        trueDestination = self.expandNode(node.trueDestination)
        falseDestination = self.expandNode(node.falseDestination)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGConditionalBranchNode, condition, trueDestination, falseDestination, predecessor = predecessor)

    @asgPatternMatchingOnNodeKind(ASGSequenceConvergenceNode)
    def expandSequenceConvergenceNode(self, node: ASGSequenceConvergenceNode) -> ASGNode:
        divergence = self.expandNode(node.divergence)
        predecessors = self.expandNodes(node.predecessors)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGSequenceConvergenceNode, divergence = divergence, predecessors = predecessors)

    @asgPatternMatchingOnNodeKind(ASGSequenceBranchEndNode)
    def expandSequenceBranchEndNode(self, node: ASGSequenceBranchEndNode) -> ASGNode:
        divergence = self.expandNode(node.divergence)
        predecessor = self.expandNode(node.predecessor)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGSequenceBranchEndNode, predecessor = predecessor, divergence = divergence)

    @asgPatternMatchingOnNodeKind(ASGAllocaNode)
    def expandAllocaNode(self, node: ASGAllocaNode) -> ASGNode:
        mirType = self.expandMirType(node.type)
        mirValueType = self.expandMirType(node.valueType)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGAllocaNode, mirType, mirValueType)

    @asgPatternMatchingOnNodeKind(ASGLoopBodyEntry)
    def expandLoopBodyEntry(self, node: ASGLoopBodyEntry) -> ASGNode:
        return node

    @asgPatternMatchingOnNodeKind(ASGLoopBreakNode)
    def expandLoopBreakNode(self, node: ASGLoopBreakNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        loopBodyEntry = self.expandNode(node.loopBodyEntry)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLoopBreakNode, predecessor, loopBodyEntry)

    @asgPatternMatchingOnNodeKind(ASGLoopContinueNode)
    def expandLoopContinueNode(self, node: ASGLoopContinueNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        loopBodyEntry = self.expandNode(node.loopBodyEntry)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLoopContinueNode, predecessor, loopBodyEntry)

    @asgPatternMatchingOnNodeKind(ASGLoopContinueEntry)
    def expandLoopContinueEntry(self, node: ASGLoopContinueEntry) -> ASGNode:
        divergence = self.expandNode(node.divergence)
        predecessors = self.expandNodes(node.predecessors)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLoopContinueEntry, divergence = divergence, predecessors = predecessors)

    @asgPatternMatchingOnNodeKind(ASGLoopEntryNode)
    def expandLoopEntryNode(self, node: ASGLoopEntryNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        entryDestination = self.expandNode(node.entryDestination)
        continueDestination = self.expandNode(node.continueDestination)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLoopEntryNode, entryDestination, continueDestination, predecessor = predecessor)

    @asgPatternMatchingOnNodeKind(ASGLoopIterationEndNode)
    def expandLoopIterationEndNode(self, node: ASGLoopIterationEndNode) -> ASGNode:
        continueCondition = self.expandNode(node.continueCondition)
        predecessor = self.expandNode(node.predecessor)
        loop = self.expandNode(node.loop)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLoopIterationEndNode, continueCondition, predecessor, loop)

    @asgPatternMatchingOnNodeKind(ASGLoadNode)
    def expandLoadNode(self, node: ASGLoadNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        pointer = self.expandNode(node.pointer)
        mirType = self.expandMirType(node.type)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGLoadNode, mirType, pointer, predecessor = predecessor)

    @asgPatternMatchingOnNodeKind(ASGStoreNode)
    def expandStoreNode(self, node: ASGStoreNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        pointer = self.expandNode(node.pointer)
        value = self.expandNode(node.value)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGStoreNode, pointer, value, predecessor = predecessor)

    @asgPatternMatchingOnNodeKind(ASGSequenceReturnNode)
    def expandSequenceReturnNode(self, node: ASGSequenceReturnNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        value = self.expandNode(node.value)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGSequenceReturnNode, value, predecessor = predecessor)

    @asgPatternMatchingOnNodeKind(ASGTypeNode)
    def expandTypeNode(self, node: ASGTypeNode) -> ASGNode:
        return node

    def expandNode(self, node: ASGNode) -> ASGNode:
        return self(node)

    def expandNodes(self, nodes: list[ASGNode]) -> ASGNode:
        return list(map(self.expandNode, nodes))

    def expandFlattenedNodes(self, nodes: list[ASGNode]):
        expandedNodes = []
        for node in nodes:
            expandedNode = self.expandNode(node)
            expandedNode.appendInFlattenedList(expandedNodes)
        return expandedNodes

def expandSourcesIntoMir(target, analyzedSources):
    expander = ASGMirExpanderAlgorithm(target)
    expandedSources = []
    for source in analyzedSources:
        expandedSources.append(expander.expandNode(source))

    expandedModuleSources = ASGModuleNode(ASGNodeNoDerivation(), expander.builder.topLevelIdentifier('Module'), expandedSources, expander.moduleExports)
    return expandedModuleSources, []

def expandModuleIntoMir(target, module):
    expander = ASGMirExpanderAlgorithm(target)
    mir = []
    for exportedValue in module.exportedValues:
        exportedValue.mirValue = expander.expandNode(exportedValue.value)
        mir.append(exportedValue.mirValue)

    expandedModuleSources = ASGModuleNode(ASGNodeNoDerivation(), expander.builder.topLevelIdentifier('Module'), mir, expander.moduleExports)
    return expandedModuleSources, []
