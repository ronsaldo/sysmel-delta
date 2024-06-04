from .mop import *
from .parsetree import *

class ASGSyntaxNode(ASGNode):
    sourceDerivation = ASGNodeSourceDerivationAttribute()
    syntacticPredecessor = ASGSyntacticPredecessorAttribute()

    def isSyntaxNode(self) -> bool:
        return True

    def isPureDataNode(self) -> bool:
        return True

    def asASGNodeDerivation(self):
        return self.sourceDerivation

class ASGSyntaxErrorNode(ASGSyntaxNode):
    message = ASGNodeDataAttribute(int)
    innerNodes = ASGNodeDataInputPorts()

class ASGSyntaxLiteralNode(ASGSyntaxNode):
    pass

class ASGSyntaxLiteralCharacterNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGSyntaxLiteralIntegerNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(int)

class ASGSyntaxLiteralFloatNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(float)

class ASGSyntaxLiteralStringNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(str)

class ASGSyntaxLiteralSymbolNode(ASGSyntaxLiteralNode):
    value = ASGNodeDataAttribute(str)

class ASGSyntaxApplicationNode(ASGSyntaxNode):
    functional = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()
    kind = ASGNodeDataAttribute(int, default = 0)

class ASGSyntaxAssignmentNode(ASGSyntaxNode):
    store = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()

class ASGSyntaxBindableNameNode(ASGSyntaxNode):
    typeExpression = ASGNodeOptionalDataInputPort()
    nameExpression = ASGNodeOptionalDataInputPort()
    isImplicit = ASGNodeDataAttribute(bool, default = False)
    isExistential = ASGNodeDataAttribute(bool, default = False)
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    isMutable = ASGNodeDataAttribute(bool, default = False)
    hasPostTypeExpression = ASGNodeDataAttribute(bool, default = False)

    def expandPatternWithValueAt(self, expander, value, location):
        return ASGSyntaxBindingDefinitionNode(ASGNodeExpansionDerivation(expander, location),
                self.typeExpression, self.nameExpression, value,
                self.isMutable)

    def parseAndUnpackArgumentsPattern(self):
        return [self], self.isExistential, self.isVariadic
    
class ASGSyntaxBindPatternNode(ASGSyntaxNode):
    pattern = ASGNodeDataInputPort()
    value = ASGNodeDataInputPort()
    allowsRebind = ASGNodeDataAttribute(bool, default = False)

class ASGSyntaxBinaryExpressionSequenceNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntaxBindingDefinitionNode(ASGSyntaxNode):
    typeExpression = ASGNodeOptionalDataInputPort()
    nameExpression = ASGNodeOptionalDataInputPort()
    valueExpression = ASGNodeDataInputPort()
    isMutable = ASGNodeDataAttribute(bool, default = False)
    allowsRebind = ASGNodeDataAttribute(bool, default = False)

class ASGSyntaxBlockNode(ASGSyntaxNode):
    functionType = ASGNodeDataInputPort()
    body = ASGNodeDataInputPorts()

class ASGSyntaxIdentifierReferenceNode(ASGSyntaxNode):
    value = ASGNodeDataAttribute(str)

class ASGSyntaxLexicalBlockNode(ASGSyntaxNode):
    body = ASGNodeDataInputPort()

class ASGSyntaxMessageSendNode(ASGSyntaxNode):
    receiver = ASGNodeOptionalDataInputPort()
    selector = ASGNodeDataInputPort()
    arguments = ASGNodeDataInputPorts()

class ASGSyntaxDictionaryNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntaxFunctionalDependentTypeNode(ASGSyntaxNode):
    argumentPattern = ASGNodeOptionalDataInputPort()
    resultType = ASGNodeOptionalDataInputPort()
    callingConvention = ASGNodeDataAttribute(str, default = None)

    def constructLambdaWithBody(self, derivation, nameExpression, body, isFixpoint):
        bodyOrInnerLambda = body
        if self.resultType is not None and self.resultType.__class__ == ASGSyntaxFunctionalDependentTypeNode:
            bodyOrInnerLambda = self.resultType.constructLambdaWithBody(derivation, None, body, False)

        argumentNodes = []
        isExistential = False
        isVariadic = False
        if self.argumentPattern is not None:
            argumentNodes, isExistential, isVariadic = self.argumentPattern.parseAndUnpackArgumentsPattern()

        return ASGSyntaxLambdaNode(derivation, nameExpression, argumentNodes, self.resultType, bodyOrInnerLambda, isVariadic = isVariadic, isFixpoint = isFixpoint, callingConvention = self.callingConvention)

class ASGSyntaxFunctionNode(ASGSyntaxNode):
    nameExpression = ASGNodeOptionalDataInputPort()
    functionalType = ASGNodeDataInputPort()
    body = ASGNodeDataInputPort()
    isFixpoint = ASGNodeDataAttribute(bool, default = False)

class ASGSyntaxLambdaNode(ASGSyntaxNode):
    nameExpression = ASGNodeOptionalDataInputPort()
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeOptionalDataInputPort()
    body = ASGNodeDataInputPort()
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    isFixpoint = ASGNodeDataAttribute(bool, default = False)
    callingConvention = ASGNodeDataAttribute(str, default = None)

class ASGSyntaxPiNode(ASGSyntaxNode):
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeOptionalDataInputPort()
    isVariadic = ASGNodeDataAttribute(bool, default = False)
    callingConvention = ASGNodeDataAttribute(str, default = None)

class ASGSyntaxSigmaNode(ASGSyntaxNode):
    arguments = ASGNodeDataInputPorts()
    resultType = ASGNodeOptionalDataInputPort()
    isVariadic = ASGNodeDataAttribute(bool, default = False)

class ASGSyntaxSequenceNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

class ASGSyntaxTupleNode(ASGSyntaxNode):
    elements = ASGNodeDataInputPorts()

    def parseAndUnpackArgumentsPattern(self):
        isExistential = False
        isVariadic = False
        if len(self.elements) == 1 and self.elements[0].isKindOf(ASGSyntaxBindableNameNode):
            isExistential = self.elements[0].isExistential
        if len(self.elements) > 0 and self.elements[-1].isKindOf(ASGSyntaxBindableNameNode):
            isVariadic = self.elements[-1].isVariadic
        return self.elements, isExistential, isVariadic

class ASGSyntaxIfThenElseNode(ASGSyntaxNode):
    condition = ASGNodeDataInputPort()
    trueExpression = ASGNodeOptionalDataInputPort()
    falseExpression = ASGNodeOptionalDataInputPort()

class ASGParseTreeFrontEnd(ParseTreeVisitor):
    def __init__(self):
        self.lastVisitedNode = None

    def visitNode(self, node: ParseTreeNode):
        self.lastVisitedNode = super().visitNode(node)
        return self.lastVisitedNode

    def visitNodeWithoutSequencing(self, node: ParseTreeNode):
        lastVisitedNode = None
        result = self.visitNode(node)
        self.lastVisitedNode = lastVisitedNode
        return result

    def transformNodesWithoutSequencing(self, nodes: list[ParseTreeNode]):
        transformed = []
        for node in nodes:
            transformed.append(self.visitNodeWithoutSequencing(node))
        return transformed

    def visitOptionalNodeWithoutSequencing(self, node: ParseTreeNode):
        if node is None:
            return None
        return self.visitNodeWithoutSequencing(node)

    def visitErrorNode(self, node: ParseTreeErrorNode):
        return ASGSyntaxErrorNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.message, self.transformNodes(node.innerNodes), syntacticPredecessor = self.lastVisitedNode)

    def visitApplicationNode(self, node: ParseTreeApplicationNode):
        return ASGSyntaxApplicationNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functional), self.transformNodesWithoutSequencing(node.arguments), node.kind, syntacticPredecessor = self.lastVisitedNode)

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        return ASGSyntaxAssignmentNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNodeWithoutSequencing(node.store), self.visitNodeWithoutSequencing(node.value), syntacticPredecessor = self.lastVisitedNode)

    def visitBindPatternNode(self, node: ParseTreeBindPatternNode):
        return ASGSyntaxBindPatternNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNodeWithoutSequencing(node.pattern), self.visitNode(node.value), syntacticPredecessor = self.lastVisitedNode, allowsRebind = True)

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        return ASGSyntaxBinaryExpressionSequenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodesWithoutSequencing(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitBindableNameNode(self, node: ParseTreeBindableNameNode):
        self.lastVisitedNode = None
        return ASGSyntaxBindableNameNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNode(node.typeExpression), self.visitOptionalNode(node.nameExpression), node.isImplicit, node.isExistential, node.isVariadic, node.isMutable, node.hasPostTypeExpression)

    def visitBlockNode(self, node: ParseTreeBlockNode):
        return ASGSyntaxBlockNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.functionType), self.visitNode(node.body), syntacticPredecessor = self.lastVisitedNode)

    def visitDictionaryNode(self, node: ParseTreeDictionaryNode):
        return ASGSyntaxDictionaryNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitFunctionalDependentTypeNode(self, node: ParseTreeFunctionalDependentTypeNode):
        return ASGSyntaxFunctionalDependentTypeNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNodeWithoutSequencing(node.argumentPattern), self.visitOptionalNodeWithoutSequencing(node.resultType), syntacticPredecessor = self.lastVisitedNode)

    def visitIdentifierReferenceNode(self, node: ParseTreeIdentifierReferenceNode):
        return ASGSyntaxIdentifierReferenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLexicalBlockNode(self, node: ParseTreeLexicalBlockNode):
        return ASGSyntaxLexicalBlockNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitNode(node.body), syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralCharacterNode(self, node: ParseTreeLiteralCharacterNode):
        return ASGSyntaxLiteralCharacterNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralFloatNode(self, node: ParseTreeLiteralFloatNode):
        return ASGSyntaxLiteralFloatNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralIntegerNode(self, node: ParseTreeLiteralIntegerNode):
        return ASGSyntaxLiteralIntegerNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralSymbolNode(self, node: ParseTreeLiteralSymbolNode):
        return ASGSyntaxLiteralSymbolNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitLiteralStringNode(self, node: ParseTreeLiteralStringNode):
        return ASGSyntaxLiteralStringNode(ASGNodeSourceCodeDerivation(node.sourcePosition), node.value, syntacticPredecessor = self.lastVisitedNode)

    def visitMessageSendNode(self, node: ParseTreeMessageSendNode):
        return ASGSyntaxMessageSendNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.visitOptionalNodeWithoutSequencing(node.receiver), self.visitNodeWithoutSequencing(node.selector), self.transformNodesWithoutSequencing(node.arguments), syntacticPredecessor = self.lastVisitedNode)

    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        return ASGSyntaxSequenceNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)

    def visitTupleNode(self, node: ParseTreeTupleNode):
        return ASGSyntaxTupleNode(ASGNodeSourceCodeDerivation(node.sourcePosition), self.transformNodes(node.elements), syntacticPredecessor = self.lastVisitedNode)
