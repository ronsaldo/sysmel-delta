from typing import Any
from .ast import *
from .value import *

class ASTEvaluator(ASTTypecheckedVisitor):
    def __init__(self, activationContext: FunctionalActivationContext) -> None:
        super().__init__()
        self.activationContext = activationContext

    def visitNode(self, node: ASTNode) -> TypedValue:
        return node.accept(self)

    def evaluate(self, ast: ASTNode) -> TypedValue:
        return self.visitNode(ast)

    def evaluateBinding(self, binding: SymbolBinding) -> TypedValue:
        return binding.evaluateInActivationContext(self.activationContext)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode) -> TypedValue:
        return node.value

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        functional = self.visitNode(node.functional)
        argument = self.visitNode(node.argument)
        return functional(argument)

    def visitTypedErrorNode(self, node: ASTTypedErrorNode) -> TypedValue:
        raise Exception('%s: %s' % (str(node.sourcePosition), node.message))

    def visitTypedForAllNode(self, node: ASTTypedForAllNode) -> TypedValue:
        type = self.visitNode(node.type)
        return ForAllValue(type, node.captureBindings, list(map(self.evaluateBinding, node.captureBindings)), node.argumentBinding, node.body)

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode) -> TypedValue:
        return self.evaluateBinding(node.binding)

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode) -> TypedValue:
        type = self.visitNode(node.type)
        return LambdaValue(type, node.captureBindings, list(map(self.evaluateBinding, node.captureBindings)), node.argumentBinding, node.body)

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode) -> TypedValue:
        return node.value

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode) -> TypedValue:
        result = UnitType.getSingleton()
        for expression in node.elements:
            result = self.visitNode(expression)
        return result

    def visitTypedTupleNode(self, node: ASTTypedTupleNode) -> TypedValue:
        elements = list()
        for expression in node.elements:
            elements.append(self.visitNode(expression))

        productType = self.visitNode(node.type)
        return productType.makeWithElements(tuple(elements))

def evaluateFunctionalValueWithParameter(functionalValue: FunctionalValue, argumentValue: TypedValue):
    activationContext = FunctionalActivationContext(functionalValue, argumentValue)
    return ASTEvaluator(activationContext).evaluate(functionalValue.body)

LambdaValue.__call__ = evaluateFunctionalValueWithParameter
ForAllValue.__call__ = evaluateFunctionalValueWithParameter
