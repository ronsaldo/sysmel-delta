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

    def visitDecoratedTypeNode(self, node: ASTDecoratedTypeNode):
        baseType = self.visitNode(node.baseType)
        return DecoratedType.makeWithDecorations(baseType, node.decorations)

    def visitPointerTypeNode(self, node: ASTPointerTypeNode):
        baseType = self.visitNode(node.baseType)
        return PointerType.makeWithBaseType(baseType)

    def visitReferenceTypeNode(self, node: ASTReferenceTypeNode):
        baseType = self.visitNode(node.baseType)
        return ReferenceType.makeWithBaseType(baseType)

    def visitTemporaryReferenceTypeNode(self, node: ASTReferenceTypeNode):
        baseType = self.visitNode(node.baseType)
        return TemporaryReferenceType.makeWithBaseType(baseType)

    def visitArrayTypeNode(self, node: ASTArrayTypeNode):
        elementType = self.visitNode(node.elementType)
        size = self.visitNode(node.size)
        return ArrayType.makeWithElementTypeAndSize(elementType, size)
    
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
        if argument.isProductTypeValue():
            return functional(*argument.elements)
        else:
            return functional(argument)
        
    def visitTypedAllocaMutableWithValueNode(self, node: ASTTypedAllocaMutableWithValueNode):
        initialValue = self.visitNode(node.initialValue)
        box = ValueBox(initialValue)
        referenceType = self.visitNode(node.type)
        return PointerLikeValue(referenceType, box, 0)
    
    def visitTypedArgumentNode(self, node: ASTTypedArgumentNode):
        assert False

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
    
    def visitTypedFunctionTypeNode(self, node: ASTTypedFunctionTypeNode) -> TypedValue:
        argumentType = self.visitNode(node.argumentType)
        resultType = self.visitNode(node.resultType)
        return FunctionType.makeFromTo(argumentType, resultType)

    def visitTypedPiNode(self, node: ASTTypedPiNode) -> TypedValue:
        type = self.visitNode(node.type)
        capturedValues = list(map(lambda binding: self.evaluateBindingAt(binding.capturedBinding, node.sourcePosition), node.captureBindings))
        argumentBindings = list(map(lambda n: n.binding, node.arguments))
        return PiValue(type, argumentBindings, node.captureBindings, capturedValues, node.body, node.sourcePosition, node.callingConvention)

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode) -> TypedValue:
        type = self.visitNode(node.type)
        capturedValues = list(map(lambda binding: self.evaluateBindingAt(binding.capturedBinding, node.sourcePosition), node.captureBindings))
        argumentBindings = list(map(lambda n: n.binding, node.arguments))
        return SigmaValue(type, argumentBindings, node.captureBindings, capturedValues, node.body, node.sourcePosition, node.callingConvention)

    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode) -> TypedValue:
        return self.evaluateBindingAt(node.binding, node.sourcePosition)

    def visitTypedIfNode(self, node: ASTTypedIfNode) -> TypedValue:
        condition = self.visitNode(node.condition)
        if condition.interpretAsBoolean():
            return self.visitNode(node.trueExpression)
        else:
            return self.visitNode(node.falseExpression)

    def visitTypedBreakNode(self, node: ASTTypedIfNode) -> TypedValue:
        assert False

    def visitTypedContinueNode(self, node: ASTTypedIfNode) -> TypedValue:
        assert False

    def visitTypedDoWhileNode(self, node: ASTTypedWhileNode) -> TypedValue:
        shouldContinue = True
        while shouldContinue:
            self.visitNode(node.bodyExpression)
            shouldContinue = self.visitNode(node.condition).interpretAsBoolean()
            if shouldContinue:
                self.visitNode(node.continueExpression)
        return VoidType.getSingleton()            

    def visitTypedWhileNode(self, node: ASTTypedWhileNode) -> TypedValue:
        while self.visitNode(node.condition).interpretAsBoolean():
            self.visitNode(node.bodyExpression)
            self.visitNode(node.continueExpression)
        return VoidType.getSingleton()            

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode) -> TypedValue:
        type = self.visitNode(node.type)
        capturedValues = list(map(lambda binding: self.evaluateBindingAt(binding.capturedBinding, node.sourcePosition), node.captureBindings))
        argumentBindings = list(map(lambda n: n.binding, node.arguments))
        return LambdaValue(type, argumentBindings, node.captureBindings, capturedValues, node.body, node.sourcePosition)

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode) -> TypedValue:
        return node.value

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode) -> TypedValue:
        value = self.visitNode(node.valueExpression)
        self.activationEnvironment.setBindingValue(node.binding, value)
        if node.isPublic:
            node.module.exportValue(node.binding.name, value)
        return value

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode) -> TypedValue:
        alternatives = list()
        for alternative in node.alternatives:
            alternatives.append(self.visitNode(alternative))

        overloadFunctionType = self.visitNode(node.type)
        return overloadFunctionType.makeWithAlternatives(tuple(alternatives))

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode) -> TypedValue:
        result = VoidType.getSingleton()
        for expression in node.elements:
            result = self.visitNode(expression)
        return result

    def visitTypedTupleNode(self, node: ASTTypedTupleNode) -> TypedValue:
        elements = list()
        for expression in node.elements:
            elements.append(self.visitNode(expression))

        productType = self.visitNode(node.type)
        return productType.makeWithElements(tuple(elements))

    def visitTypedTupleAtNode(self, node: ASTTypedTupleAtNode) -> TypedValue:
        tuple = self.visitNode(node.tuple)
        return tuple[node.index]

    def visitTypedFromModuleImportNode(self, node: ASTTypedFromModuleImportNode):
        module = self.visitNode(node.module)
        type = self.visitNode(node.type)
        return module.importValueWithType(node.name, type)

    def visitTypedFromExternalImportWithTypeNode(self, node: ASTTypedFromExternalImportWithTypeNode):
        type = self.visitNode(node.type)
        return ImportedExternalValue(node.externalName, node.name, type)

    def visitTypedModuleExportValueNode(self, node: ASTTypedModuleExportValueNode):
        value = self.visitNode(node.value)
        node.module.exportValue(node.name, value, node.externalName)
        return value

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode) -> TypedValue:
        entryPoint = self.visitNode(node.entryPoint)
        node.module.entryPoint = entryPoint
        return entryPoint

def evaluateFunctionalValueWithParameters(functionalValue: FunctionalValue, *argumentValues: TypedValue):
    activationEnvironment = FunctionalActivationEnvironment()
    for i in range(len(functionalValue.argumentBindings)):
        activationEnvironment.setBindingValue(functionalValue.argumentBindings[i], argumentValues[i])
    for i in range(len(functionalValue.captureBindings)):
        activationEnvironment.setBindingValue(functionalValue.captureBindings[i], functionalValue.captureBindingValues[i])

    return ASTEvaluator(activationEnvironment).evaluate(functionalValue.body)

LambdaValue.__call__ = evaluateFunctionalValueWithParameters
PiValue.__call__ = evaluateFunctionalValueWithParameters
