from typing import Any
from .ast import *
from .value import *

class ASTEvaluator(ASTTypecheckedVisitor):
    def __init__(self, activationEnvironment: FunctionalActivationEnvironment) -> None:
        super().__init__()
        self.activationEnvironment = activationEnvironment

    def visitNode(self, node: ASTNode) -> TypedValue:
        return node.accept(self)

    def evaluate(self, ast: ASTNode) -> TypedValue:
        return self.visitNode(ast)

    def evaluateBindingAt(self, binding: SymbolBinding, sourcePosition: SourcePosition) -> TypedValue:
        return binding.evaluateInActivationEnvironmentAt(self.activationEnvironment, sourcePosition)

    def visitLiteralTypeNode(self, node: ASTLiteralTypeNode) -> TypedValue:
        return node.value

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        functional = self.visitNode(node.functional)
        argument = self.visitNode(node.argument)
        return functional(argument)

    def visitTypedErrorNode(self, node: ASTTypedErrorNode) -> TypedValue:
        raise Exception('%s: %s' % (str(node.sourcePosition), node.message))

    def visitTypedPiNode(self, node: ASTTypedPiNode) -> TypedValue:
        type = self.visitNode(node.type)
        return PiValue(type, self.activationEnvironment, node.argumentBinding, node.body)

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode) -> TypedValue:
        return self.evaluateBindingAt(node.binding, node.sourcePosition)

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode) -> TypedValue:
        type = self.visitNode(node.type)
        return LambdaValue(type, self.activationEnvironment, node.argumentBinding, node.body)

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode) -> TypedValue:
        return node.value

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode) -> TypedValue:
        alternatives = list()
        for alternative in node.alternatives:
            alternatives.append(self.visitNode(alternative))

        overloadFunctionType = self.visitNode(node.type)
        return overloadFunctionType.makeWithAlternatives(tuple(alternatives))

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
    activationEnvironment = FunctionalActivationEnvironment(functionalValue.environment)
    activationEnvironment.setBindingValue(functionalValue.argumentBinding, argumentValue)
    return ASTEvaluator(activationEnvironment).evaluate(functionalValue.body)

LambdaValue.__call__ = evaluateFunctionalValueWithParameter
PiValue.__call__ = evaluateFunctionalValueWithParameter
