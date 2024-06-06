from .mop import *
from .environment import *
from .asg import *

class ASGNodeMirExpansionDerivation(ASGNodeExpansionDerivation):
    pass

class ASGMirReductionAlgorithm(ASGDynamicProgrammingReductionAlgorithm):
    def __init__(self) -> None:
        super().__init__()

class ASGMirTypeExpansionAlgorithm(ASGDynamicProgrammingAlgorithm):
    def __init__(self, builder: ASGBuilderWithGVN) -> None:
        super().__init__()
        self.builder = builder

    @asgPatternMatchingOnNodeKind(ASGArrayTypeNode)
    def expandArrayTypeNode(self, node: ASGArrayTypeNode) -> ASGNode:
        baseType = self.expandNode(node.baseType)

        if not node.size.isLiteralNode():
            return self.builder.forMirTypeExpansionBuild(self, node, ASGPointerTypeNode, baseType)
        
        if baseType.unificationEquals(node.baseType):
            return node

        return self.builder.forMirTypeExpansionBuild(self, node, ASGArrayTypeNode, baseType, node.size)

    @asgPatternMatchingOnNodeKind(ASGPiNode)
    def expandPiNode(self, node: ASGPiNode) -> ASGNode:
        resultType = self.expandNode(node.resultType)

        argumentTypes = []
        for argument in node.arguments:
            assert argument.isArgumentNode()
            self.expandNode(argument.type).appendInFlattenedList(argumentTypes)

        functionType = self.builder.forMirTypeExpansionBuild(self, node, ASGMirFunctionTypeNode, argumentTypes, resultType, isVariadic = node.isVariadic, callingConvention = node.callingConvention, pure = node.pure)
        return self.builder.forMirTypeExpansionBuild(self, node, ASGMirClosureTypeNode, functionType)

    @asgPatternMatchingOnNodeKind(ASGTypeNode)
    def expandTypeNode(self, node: ASGTypeNode) -> ASGNode:
        return node
    
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

    @asgPatternMatchingOnNodeKind(ASGLiteralNode)
    def expandLiteralNode(self, node: ASGLiteralNode) -> ASGNode:
        return node

    @asgPatternMatchingOnNodeKind(ASGTopLevelScriptNode)
    def expandSyntaxFromExternalImportNode(self, node: ASGTopLevelScriptNode) -> ASGNode:
        type = self.expandNode(node.type)
        entryPoint = self.expandNode(node.entryPoint)
        result = self.expandNode(node.result)
        exitPoint = self.expandNode(node.exitPoint)

        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGTopLevelScriptNode, type, entryPoint, result, exitPoint)

    @asgPatternMatchingOnNodeKind(ASGFromExternalImportNode)
    def expandFromExternalImportNode(self, node: ASGFromExternalImportNode) -> ASGNode:
        mirType = self.expandMirType(node.type)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGMirFromExternalImportNode, node.type, mirType, node.externalName, node.importedName)
    
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
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGMirArgumentNode, node.type, mirType, node.index, node.name, node.isImplicit)

    @asgPatternMatchingOnNodeKind(ASGApplicationNode)
    def expandApplicationNode(self, node: ASGApplicationNode) -> ASGNode:
        mirType = self.expandMirType(node.type)
        functional = self.expandNode(node.functional)
        arguments = self.expandFlattenedNodes(node.arguments)

        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGMirApplicationNode, node.type, mirType, functional, arguments)

    @asgPatternMatchingOnNodeKind(ASGFxApplicationNode)
    def expandFxApplicationNode(self, node: ASGFxApplicationNode) -> ASGNode:
        predecessor = self.expandNode(node.predecessor)
        mirType = self.expandMirType(node.type)
        functional = self.expandNode(node.functional)
        arguments = self.expandFlattenedNodes(node.arguments)

        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGMirFxApplicationNode, node.type, mirType, functional, arguments, predecessor = predecessor)

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
        result = definitionExpander.expandNode(node.result)
        exitPoint = definitionExpander.expandNode(node.exitPoint)

        definition = self.builder.forMirExpansionBuildAndSequence(self, node, ASGMirFunctionDefinitionNode, node.type, mirType.functionType, arguments, entryPoint, result, node.callingConvention, exitPoint = exitPoint)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGMirLambdaNode, node.type, mirType, definition, [])

    @asgPatternMatchingOnNodeKind(ASGSequenceEntryNode)
    def expandSequenceEntryNode(self, node: ASGTypeNode) -> ASGNode:
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
        values = self.expandNodes(node.values)
        return self.builder.forMirExpansionBuildAndSequence(self, node, ASGSequenceConvergenceNode, values, divergence = divergence, predecessors = predecessors)
    
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
