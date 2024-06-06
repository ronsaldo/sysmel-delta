from .mop import *
from .asg import *

class GlobalCodeMotionAlgorithm:
    def __init__(self, functionalNode) -> None:
        self.functionalNode = functionalNode
        self.regions = []
        self.regionToIndexDictionary = {}
        self.dataInstructions = []
        self.idoms = []
        self.dominanceTreeDepths = []

    def computeForLambda(self):
        lambdaNode: ASGLambdaNode = self.functionalNode
        self.computeForRegions(asgPredecessorTopo(lambdaNode.exitPoint))
        return self

    def computeForRegions(self, regions):
        self.regions = regions
        self.findDataInstructions()
        for i in range(len(regions)):
            region = regions[i]
            self.regionToIndexDictionary[region] = i

        # The direct immediate dominators are missing the divergence destinations.
        self.idoms = list(map(lambda r: r.directImmediateDominator(), regions))
        for region in regions:
            for divergenceDestination in region.divergenceDestinations():
                destinationIndex = self.regionToIndexDictionary[divergenceDestination]
                assert self.idoms[destinationIndex] is None
                self.idoms[destinationIndex] = region

        # Dominance tree depths.
        self.dominanceTreeDepths = [None] * len(regions)
        for i in range(len(regions)):
            self.computeDominanceTreeDepthAtIndex(i)

        pass


    def findDataInstructions(self):
        visited = set()
        self.dataInstructions = []
        self.constantDataInstructions = []
        
        def traverseNode(node):
            if node in visited:
                return
            
            visited.add(node)
            if not node.isConstantDataNode():
                for dependency in node.dataDependencies():
                    if dependency in visited:
                        continue

                    traverseNode(dependency)

            if node.isPureDataNode():
                if node.isConstantDataNode():
                    self.constantDataInstructions.append(node)
                else:
                    self.dataInstructions.append(node)

        for region in self.regions:
            traverseNode(region)

    def computeDominanceTreeDepthAtIndex(self, index):
        if self.dominanceTreeDepths[index] is None:
            idom = self.idoms[index]
            if idom is None:
                self.dominanceTreeDepths[index] = 0
            else:
                idomIndex = self.regionToIndexDictionary[idom]
                self.dominanceTreeDepths[index] = self.computeDominanceTreeDepthAtIndex(idomIndex) + 1
        
        return self.dominanceTreeDepths[index]

def lambdaGCM(node: ASGLambdaNode):
    lambdaWithGcm = GlobalCodeMotionAlgorithm(node).computeForLambda()
    return lambdaWithGcm
