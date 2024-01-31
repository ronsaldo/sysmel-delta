from typing import Any
from .ast import *
from .value import *
from .environment import *

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

    def visitOverloadsTypeNode(self, node: ASTOverloadsTypeNode):
        alternativeTypes = []
        for alternativeType in node.alternativeTypes:
            alternativeTypes.append(self.visitNode(alternativeType))
        return OverloadsType.makeWithAlternativeTypes(alternativeTypes)

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        elementTypes = []
        for elementType in node.elementTypes:
            elementTypes.append(self.visitNode(elementType))
        return ProductType.makeWithElementTypes(elementTypes)

    def visitSumTypeNode(self, node: ASTSumTypeNode):
        alternativeTypes = []
        for alternativeType in node.alternativeTypes:
            alternativeTypes.append(self.visitNode(alternativeType))
        return SumType.makeWithElementTypes(alternativeTypes)

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        for implicitBinding, implicitValueNode in node.implicitValueSubstitutions:
            implicitValue = self.visitNode(implicitValueNode)
            self.activationEnvironment.setBindingValue(implicitBinding, implicitValue)

        functional = self.visitNode(node.functional)
        argument = self.visitNode(node.argument)
        return functional(argument)

    def visitTypedOverloadedApplicationNode(self, node: ASTTypedOverloadedApplicationNode):
        type = self.visitNode(node.type)
        overloads: OverloadsTypeValue = self.visitNode(node.overloads)
        argument = self.visitNode(node.argument)

        selectedOverloads = []
        for alternativeIndex in node.alternativeIndices:
            alternative = overloads.alternatives[alternativeIndex]
            selectedOverloads.append(alternative(argument))
        return type.makeWithAlternatives(selectedOverloads)

    def visitTypedErrorNode(self, node: ASTTypedErrorNode) -> TypedValue:
        raise Exception('%s: %s' % (str(node.sourcePosition), node.message))

    def visitTypedPiNode(self, node: ASTTypedPiNode) -> TypedValue:
        type = self.visitNode(node.type)
        capturedValues = list(map(lambda binding: self.evaluateBindingAt(binding.capturedBinding, node.sourcePosition), node.captureBindings))
        return PiValue(type, node.argumentBinding, node.captureBindings, capturedValues, node.body, node.sourcePosition)

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode) -> TypedValue:
        type = self.visitNode(node.type)
        capturedValues = list(map(lambda binding: self.evaluateBindingAt(binding.capturedBinding, node.sourcePosition), node.captureBindings))
        return SigmaValue(type, node.argumentBinding, node.captureBindings, capturedValues, node.body, node.sourcePosition)

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode) -> TypedValue:
        return self.evaluateBindingAt(node.binding, node.sourcePosition)

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode) -> TypedValue:
        type = self.visitNode(node.type)
        capturedValues = list(map(lambda binding: self.evaluateBindingAt(binding.capturedBinding, node.sourcePosition), node.captureBindings))
        return LambdaValue(type, node.argumentBinding, node.captureBindings, capturedValues, node.body, node.sourcePosition)

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode) -> TypedValue:
        return node.value

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode) -> TypedValue:
        value = self.visitNode(node.valueExpression)
        self.activationEnvironment.setBindingValue(node.binding, value)
        if node.isPublic:
            node.module.setExportedBindingValue(node.binding, value)
        return value

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

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode) -> TypedValue:
        entryPoint = self.visitNode(node.entryPoint)
        node.module.entryPoint = entryPoint
        return entryPoint

def evaluateFunctionalValueWithParameter(functionalValue: FunctionalValue, argumentValue: TypedValue):
    activationEnvironment = FunctionalActivationEnvironment()
    activationEnvironment.setBindingValue(functionalValue.argumentBinding, argumentValue)
    for i in range(len(functionalValue.captureBindings)):
        activationEnvironment.setBindingValue(functionalValue.captureBindings[i], functionalValue.captureBindingValues[i])

    return ASTEvaluator(activationEnvironment).evaluate(functionalValue.body)

LambdaValue.__call__ = evaluateFunctionalValueWithParameter
PiValue.__call__ = evaluateFunctionalValueWithParameter
