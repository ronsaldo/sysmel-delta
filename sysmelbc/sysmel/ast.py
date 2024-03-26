from .value import *
from abc import ABC, abstractmethod

class ASTVisitor(ABC):
    @abstractmethod
    def visitApplicationNode(self, node):
        pass

    @abstractmethod
    def visitAllocaMutableWithValueNode(self, node):
        pass

    @abstractmethod
    def visitArgumentNode(self, node):
        pass

    @abstractmethod
    def visitArgumentApplicationNode(self, node):
        pass

    @abstractmethod
    def visitBinaryExpressionSequenceNode(self, node):
        pass

    @abstractmethod
    def visitErrorNode(self, node):
        pass

    @abstractmethod
    def visitPiNode(self, node):
        pass

    @abstractmethod
    def visitSigmaNode(self, node):
        pass

    @abstractmethod
    def visitFunctionNode(self, node):
        pass

    @abstractmethod
    def visitFunctionTypeNode(self, node):
        pass

    @abstractmethod
    def visitFunctionalDependentTypeNode(self, node):
        pass

    @abstractmethod
    def visitIdentifierReferenceNode(self, node):
        pass

    @abstractmethod
    def visitIfNode(self, node):
        pass

    @abstractmethod
    def visitBreakNode(self, node):
        pass

    @abstractmethod
    def visitContinueNode(self, node):
        pass

    @abstractmethod
    def visitDoWhileNode(self, node):
        pass

    @abstractmethod
    def visitWhileNode(self, node):
        pass

    @abstractmethod
    def visitOverloadsNode(self, node):
        pass

    @abstractmethod
    def visitLambdaNode(self, node):
        pass

    @abstractmethod
    def visitLexicalBlockNode(self, node):
        pass

    @abstractmethod
    def visitLiteralNode(self, node):
        pass

    @abstractmethod
    def visitLiteralTypeNode(self, node):
        pass

    @abstractmethod
    def visitBindingDefinitionNode(self, node):
        pass

    @abstractmethod
    def visitMessageSendNode(self, node):
        pass

    @abstractmethod
    def visitImportModuleNode(self, node):
        pass
    
    @abstractmethod
    def visitFromModuleImportWithTypeNode(self, node):
        pass

    @abstractmethod
    def visitFromExternalImportWithTypeNode(self, node):
        pass

    @abstractmethod
    def visitModuleExportValueNode(self, node):
        pass

    @abstractmethod
    def visitModuleEntryPointNode(self, node):
        pass

    @abstractmethod
    def visitOverloadsTypeNode(self, node):
        pass

    @abstractmethod
    def visitProductTypeNode(self, node):
        pass

    @abstractmethod
    def visitSumTypeNode(self, node):
        pass

    @abstractmethod
    def visitSequenceNode(self, node):
        pass

    @abstractmethod
    def visitTupleNode(self, node):
        pass

    @abstractmethod
    def visitTypedApplicationNode(self, node):
        pass

    @abstractmethod
    def visitTypedAllocaMutableWithValueNode(self, node):
        pass

    @abstractmethod
    def visitTypedArgumentNode(self, node):
        pass

    @abstractmethod
    def visitTypedErrorNode(self, node):
        pass

    @abstractmethod
    def visitTypedFunctionTypeNode(self, node):
        pass

    @abstractmethod
    def visitTypedPiNode(self, node):
        pass

    @abstractmethod
    def visitTypedSigmaNode(self, node):
        pass

    @abstractmethod
    def visitTypedIdentifierReferenceNode(self, node):
        pass

    @abstractmethod
    def visitTypedIfNode(self, node):
        pass

    @abstractmethod
    def visitTypedBreakNode(self, node):
        pass

    @abstractmethod
    def visitTypedContinueNode(self, node):
        pass

    @abstractmethod
    def visitTypedDoWhileNode(self, node):
        pass

    @abstractmethod
    def visitTypedWhileNode(self, node):
        pass

    @abstractmethod
    def visitTypedLambdaNode(self, node):
        pass

    @abstractmethod
    def visitTypedLiteralNode(self, node):
        pass

    @abstractmethod
    def visitTypedBindingDefinitionNode(self, node):
        pass

    @abstractmethod
    def visitTypedOverloadedApplicationNode(self, node):
        pass

    @abstractmethod
    def visitTypedOverloadsNode(self, node):
        pass

    @abstractmethod
    def visitTypedSequenceNode(self, node):
        pass

    @abstractmethod
    def visitTypedTupleNode(self, node):
        pass

    @abstractmethod
    def visitTypedTupleAtNode(self, node):
        pass

    @abstractmethod
    def visitTypedFromModuleImportNode(self, node):
        pass

    @abstractmethod
    def visitTypedFromExternalImportWithTypeNode(self, node):
        pass

    @abstractmethod
    def visitTypedModuleExportValueNode(self, node):
        pass

    @abstractmethod
    def visitTypedModuleEntryPointNode(self, node):
        pass

class ASTAllocaMutableWithValueNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, initialValue: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.initialValue = initialValue

    def accept(self, visitor: ASTVisitor):
        return visitor.visitAllocaMutableWithValueNode(self)

    def toJson(self) -> dict:
        return {'kind': 'AllocaMutableWithValue', 'initialValue': self.initialValue.toJson()}

class ASTArgumentNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, typeExpression: ASTNode, nameExpression: ASTNode, isImplicit: bool = False, isExistential: bool = False) -> None:
        super().__init__(sourcePosition)
        self.typeExpression = typeExpression
        self.nameExpression = nameExpression
        self.isImplicit = isImplicit
        self.isExistential = isExistential

    def isArgumentNode(self) -> bool:
        return True

    def accept(self, visitor: ASTVisitor):
        return visitor.visitArgumentNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Argument', 'typeExpression': optionalASTNodeToJson(self.typeExpression), 'nameExpression': optionalASTNodeToJson(self.nameExpression), 'isImplicit': self.isImplicit, 'isExistential': self.isExistential}

class ASTArgumentApplicationNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, functional: ASTNode, argument: ASTNode, isImplicit = False) -> None:
        super().__init__(sourcePosition)
        self.functional = functional
        self.argument = argument
        self.isImplicit = isImplicit

    def accept(self, visitor: ASTVisitor):
        return visitor.visitArgumentApplicationNode(self)

    def toJson(self) -> dict:
        return {'kind': 'ArgumentApplication', 'functional': self.functional.toJson(), 'argument': self.argument.toJson()}
    
class ASTApplicationNode(ASTNode):
    Normal = 0
    Bracket = 1
    CurlyBracket = 2

    def __init__(self, sourcePosition: SourcePosition, functional: ASTNode, arguments: list[ASTNode], kind = Normal) -> None:
        super().__init__(sourcePosition)
        self.functional = functional
        self.arguments = arguments
        self.kind = kind

    def accept(self, visitor: ASTVisitor):
        return visitor.visitApplicationNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Application', 'functional': self.functional.toJson(), 'arguments': list(map(optionalASTNodeToJson, self.arguments)), 'kind': self.kind}

class ASTBinaryExpressionSequenceNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitBinaryExpressionSequenceNode(self)

    def toJson(self) -> dict:
        return {'kind': 'BinaryExpressionSequence', 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTErrorNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, message: str) -> None:
        super().__init__(sourcePosition)
        self.message = message

    def accept(self, visitor: ASTVisitor):
        return visitor.visitErrorNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Error', 'message': self.message}

class ASTFunctionalDependentTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, arguments: list[ASTNode], tupleArguments: list[ASTNode], isVariadic: bool, resultType: ASTNode, callingConvention: Symbol = None) -> None:
        super().__init__(sourcePosition)
        self.arguments = arguments
        self.tupleArguments = tupleArguments
        self.isVariadic = isVariadic
        self.resultType = resultType
        self.callingConvention = callingConvention

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFunctionalDependentTypeNode(self)
    
    def isFunctionalDependentTypeNode(self) -> bool:
        return True

    def withCallingConventionNamed(self, callingConventionName: TypedValue):
        if callingConventionName == self.callingConvention:
            return self
        return ASTFunctionalDependentTypeNode(self.sourcePosition, self.arguments, self.tupleArguments, self.isVariadic, self.resultType, callingConventionName)
    
    def toJson(self) -> dict:
        return {'kind': 'FunctionalType', 'arguments': list(map(optionalASTNodeToJson, self.arguments)), 'resultType': optionalASTNodeToJson(self.resultType)}

class ASTIdentifierReferenceNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, value: Symbol) -> None:
        super().__init__(sourcePosition)
        self.value = value

    def accept(self, visitor: ASTVisitor):
        return visitor.visitIdentifierReferenceNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Identifier', 'value': repr(self.value)}

class ASTIfNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, condition: ASTNode, trueExpression: ASTNode, falseExpression: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.condition = condition
        self.trueExpression = trueExpression
        self.falseExpression = falseExpression
    
    def accept(self, visitor: ASTVisitor):
        return visitor.visitIfNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'If', 'condition': self.condition.toJson(), 'trueExpression' : optionalASTNodeToJson(self.trueExpression), 'falseExpression' : optionalASTNodeToJson(self.falseExpression)}

class ASTBreakNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition) -> None:
        super().__init__(sourcePosition)
    
    def accept(self, visitor: ASTVisitor):
        return visitor.visitBreakNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'Break'}

class ASTContinueNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition) -> None:
        super().__init__(sourcePosition)
    
    def accept(self, visitor: ASTVisitor):
        return visitor.visitContinueNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'Continue'}

class ASTDoWhileNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, bodyExpression: ASTNode, condition: ASTNode, continueExpression: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.bodyExpression = bodyExpression
        self.condition = condition
        self.continueExpression = continueExpression
    
    def accept(self, visitor: ASTVisitor):
        return visitor.visitDoWhileNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'DoWhile', 'bodyExpression' : optionalASTNodeToJson(self.bodyExpression), 'condition': optionalASTNodeToJson(self.condition.toJson()), 'continueExpression' : optionalASTNodeToJson(self.continueExpression)}

class ASTWhileNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, condition: ASTNode, bodyExpression: ASTNode, continueExpression: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.condition = condition
        self.bodyExpression = bodyExpression
        self.continueExpression = continueExpression
    
    def accept(self, visitor: ASTVisitor):
        return visitor.visitWhileNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'While', 'condition': optionalASTNodeToJson(self.condition.toJson()), 'bodyExpression' : optionalASTNodeToJson(self.bodyExpression), 'continueExpression' : optionalASTNodeToJson(self.continueExpression)}

class ASTPiNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, arguments: list[ASTNode], body: ASTNode, callingConvention: Symbol = None) -> None:
        super().__init__(sourcePosition)
        self.arguments = arguments
        self.body = body
        self.callingConvention = callingConvention

    def accept(self, visitor: ASTVisitor):
        return visitor.visitPiNode(self)

    def toJson(self) -> dict:
        return {'kind': 'PiNode', 'arguments': list(map(lambda x: x.toJson(), self.arguments)), 'body': optionalASTNodeToJson(self.body)}

class ASTSigmaNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, arguments: list[ASTNode], body: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.arguments = arguments
        self.body = body

    def accept(self, visitor: ASTVisitor):
        return visitor.visitSigmaNode(self)

    def toJson(self) -> dict:
        return {'kind': 'SigmaNode', 'arguments': list(map(lambda x: x.toJson(), self.arguments)), 'body': optionalASTNodeToJson(self.body)}

class ASTFunctionNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, functionalType: ASTFunctionalDependentTypeNode, body: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.functionalType = functionalType
        self.body = body

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFunctionNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Function', 'functionalType': self.functionalType.toJson(), 'body': self.body.toJson()}
    
class ASTLambdaNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, arguments: list[ASTArgumentNode], resultType: ASTNode, body: ASTNode, callingConvention: Symbol = None) -> None:
        super().__init__(sourcePosition)
        self.arguments = arguments
        self.resultType = resultType
        self.body = body
        self.callingConvention = callingConvention

    def accept(self, visitor: ASTVisitor):
        return visitor.visitLambdaNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Lambda', 'arguments': list(map(lambda x: x.toJson(), self.arguments)), 'resultType': optionalASTNodeToJson(self.resultType), 'body': self.body.toJson(), 'callingConvention' : optionalToJson(self.callingConvention)}

class ASTBindingDefinitionNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, nameExpression: ASTNode, expectedTypeExpression: ASTNode | None, initialValueExpression: ASTNode, isMutable = False, isPublic = False) -> None:
        super().__init__(sourcePosition)
        self.nameExpression = nameExpression
        self.expectedTypeExpression = expectedTypeExpression
        self.initialValueExpression = initialValueExpression
        self.isMutable = isMutable
        self.isPublic = isPublic

    def accept(self, visitor: ASTVisitor):
        return visitor.visitBindingDefinitionNode(self)

    def toJson(self) -> dict:
        return {'kind': 'BindingDefinitionNode', 'nameExpression': optionalASTNodeToJson(self.nameExpression), 'expectedTypeExpression': optionalASTNodeToJson(self.expectedTypeExpression), 'initialValueExpression': optionalASTNodeToJson(self.initialValueExpression)}

class ASTBlockNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, functionalType: ASTFunctionalDependentTypeNode, body: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.functionalType = functionalType
        self.body = body

    def accept(self, visitor: ASTVisitor):
        return visitor.visitBlockNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Block', 'functionalType': self.functionalType.toJson(), 'body': self.body.toJson()}

class ASTLexicalBlockNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, expression: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.expression = expression

    def accept(self, visitor: ASTVisitor):
        return visitor.visitLexicalBlockNode(self)

    def toJson(self) -> dict:
        return {'kind': 'LexicalBlock', 'expression': self.expression.toJson()}

class ASTLiteralNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, value: TypedValue) -> None:
        super().__init__(sourcePosition)
        self.value = value

    def accept(self, visitor: ASTVisitor):
        return visitor.visitLiteralNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Literal', 'value': self.value.toJson()}

class ASTFunctionTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, argumentType: ASTNode, resultType: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.argumentType = argumentType
        self.resultType = resultType

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFunctionTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'FunctionType', 'argument': self.argumentType.toJson(), 'result' : self.resultType.toJson()}
    
class ASTMessageSendNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, receiver: ASTNode, selector: ASTNode, arguments: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.receiver = receiver
        self.selector = selector
        self.arguments = arguments

    def accept(self, visitor: ASTVisitor):
        return visitor.visitMessageSendNode(self)

    def isMessageSendNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'MessageSend', 'receiver': optionalASTNodeToJson(self.receiver), 'selector': self.selector.toJson(), 'arguments': list(map(optionalASTNodeToJson, self.arguments))}

class ASTSequenceNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitSequenceNode(self)

    def toJson(self):
        return {'kind': 'Sequence', 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTOverloadsNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, alternatives: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.alternatives = alternatives

    def accept(self, visitor: ASTVisitor):
        return visitor.visitOverloadsNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Overloads', 'elements': list(map(optionalASTNodeToJson, self.alternatives))}

class ASTTupleNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTupleNode(self)
    
    def isTupleNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'Tuple', 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTOverloadsTypeNode(ASTTypeNode):
    def __init__(self, sourcePosition: SourcePosition, alternativeTypes: list[ASTTypeNode]) -> None:
        super().__init__(sourcePosition)
        self.alternativeTypes = alternativeTypes
        self.typeUniverseIndex = None

    def computeTypeUniverseIndex(self) -> int:
        if self.typeUniverseIndex is None:
            self.typeUniverseIndex = -1
            for alternativeType in self.alternativeTypes:
                self.typeUniverseIndex = max(self.typeUniverseIndex, alternativeType.computeTypeUniverseIndex())
        
        return self.typeUniverseIndex
    
    def isOverloadsTypeNode(self) -> bool:
        return True
    
    def accept(self, visitor):
        return visitor.visitOverloadsTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'OverloadsType', 'alternativeTypes': list(map(optionalASTNodeToJson, self.alternativeTypes))}
    
class ASTProductTypeNode(ASTTypeNode):
    def __init__(self, sourcePosition: SourcePosition, elementTypes: list[ASTTypeNode]) -> None:
        super().__init__(sourcePosition)
        self.elementTypes = elementTypes
        self.typeUniverseIndex = None

    def computeTypeUniverseIndex(self) -> int:
        if self.typeUniverseIndex is None:
            self.typeUniverseIndex = -1
            for elementType in self.elementTypes:
                self.typeUniverseIndex = max(self.typeUniverseIndex, elementType.computeTypeUniverseIndex())
        
        return self.typeUniverseIndex
    
    def accept(self, visitor):
        return visitor.visitProductTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'ProductType', 'elementTypes': list(map(optionalASTNodeToJson, self.elementTypes))}
    
class ASTSumTypeNode(ASTTypeNode):
    def __init__(self, sourcePosition: SourcePosition, alternativeTypes: list[ASTTypeNode]) -> None:
        super().__init__(sourcePosition)
        self.alternativeTypes = alternativeTypes
        self.typeUniverseIndex = None

    def computeTypeUniverseIndex(self) -> int:
        if self.typeUniverseIndex is None:
            self.typeUniverseIndex = -1
            for alternativeType in self.alternativeTypes:
                self.typeUniverseIndex = max(self.typeUniverseIndex, alternativeType.computeTypeUniverseIndex())
        
        return self.typeUniverseIndex
    
    def accept(self, visitor):
        return visitor.visitSumTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'SumType', 'alternativeTypes': list(map(optionalASTNodeToJson, self.alternativeTypes))}

class ASTImportModuleNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, name: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.name = name
    
    def accept(self, visitor):
        return visitor.visitImportModuleNode(self)

    def toJson(self) -> dict:
        return {'kind': 'ImportModule', 'name': self.name.toJson()}

class ASTFromExternalImportWithTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, externalName: ASTNode, name: ASTNode, type: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.externalName = externalName
        self.name = name
        self.type = type
    
    def accept(self, visitor):
        return visitor.visitFromExternalImportWithTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'FromExternalImportWithType', 'externalName': self.externalName.toJson(), 'name': self.name.toJson(), 'type': self.type.toJson()}

class ASTFromModuleImportWithTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, module: ASTNode, name: ASTNode, type: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.module = module
        self.name = name
        self.type = type
    
    def accept(self, visitor):
        return visitor.visitFromModuleImportWithTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'FromModuleImportWithType', 'module': self.module.toJson(), 'name': self.name.toJson(), 'type': self.type.toJson()}

class ASTModuleExportValueNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, externalName: ASTNode | None, name: ASTNode, value: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.externalName = externalName
        self.name = name
        self.value = value
    
    def accept(self, visitor):
        return visitor.visitModuleExportValueNode(self)

    def toJson(self) -> dict:
        return {'kind': 'ModuleExport', 'externalName': optionalASTNodeToJson(self.externalName), 'name': self.name.toJson(), 'value:' : self.value}

class ASTModuleEntryPointNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, entryPoint: ASTTypeNode) -> None:
        super().__init__(sourcePosition)
        self.entryPoint = entryPoint
    
    def accept(self, visitor):
        return visitor.visitModuleEntryPointNode(self)

    def toJson(self) -> dict:
        return {'kind': 'ModuleEntryPoint', 'entryPoint': self.entryPoint.toJson()}

class ASTTypedAllocaMutableWithValueNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, initialValue: ASTNode) -> None:
        super().__init__(sourcePosition, type)
        self.initialValue = initialValue

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedAllocaMutableWithValueNode(self)

    def toJson(self) -> dict:
        return {'kind': 'AllocaMutableWithValue', 'type' : self.type.toJson(), 'initialValue': self.initialValue.toJson()}
    
class ASTTypedArgumentNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, binding: SymbolArgumentBinding, isImplicit: bool = False, isExistential: bool = False) -> None:
        super().__init__(sourcePosition, type)
        self.binding = binding
        self.isImplicit = isImplicit
        self.isExistential = isExistential

    def isTypedArgumentNode(self) -> bool:
        return True

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedArgumentNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedArgument', 'type': self.type.toJson(), 'name': self.name.toJson(), 'isImplicit': self.isImplicit, 'isExistential': self.isExistential}

class ASTTypedApplicationNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, functional: ASTTypedNode, argument: ASTTypedNode, implicitValueSubstitutions: list[tuple[SymbolBinding, ASTNode]]) -> None:
        super().__init__(sourcePosition, type)
        self.functional = functional
        self.argument = argument
        self.implicitValueSubstitutions = implicitValueSubstitutions

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedApplicationNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedApplication', 'type': self.type.toJson(), 'functional': self.functional.toJson(), 'argument': self.argument.toJson()}

class ASTTypedOverloadedApplicationNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, overloads: ASTTypedNode, alternativeImplicitValueSubstitutions: list[tuple[SymbolImplicitValueBinding, ASTNode]], argument: ASTTypedNode, alternativeIndices: list[int]) -> None:
        super().__init__(sourcePosition, type)
        self.overloads = overloads
        self.alternativeImplicitValueSubstitutions = alternativeImplicitValueSubstitutions
        self.argument = argument
        self.alternativeIndices = alternativeIndices

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedOverloadedApplicationNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedOverloadedApplication', 'type': self.type.toJson(), 'overloads': self.overloads.toJson(), 'alternativeArguments': list(map(optionalASTNodeToJson, self.alternativeArguments)), 'alternativeIndices': self.alternativeIndices}

class ASTTypedErrorNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, message: str, innerNodes: list[ASTNode]) -> None:
        super().__init__(sourcePosition, type)
        self.message = message
        self.innerNodes = innerNodes

    def isTypedErrorNode(self) -> bool:
        return True

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedErrorNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedError', 'type': self.type.toJson(), 'message': self.message, 'innerNodes': list(map(optionalASTNodeToJson, self.innerNodes))}

class ASTTypedFunctionTypeNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, argumentType: ASTTypedNode, resultType: ASTTypedNode) -> None:
        super().__init__(sourcePosition, type)
        self.argumentType = argumentType
        self.resultType = resultType

    def isTypedFunctionTypeNode(self) -> bool:
        return True

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedFunctionTypeNode(self)
    
    def asTypedFunctionTypeNodeAtFor(self, sourcePosition, typechecker):
        return self

    def toJson(self) -> dict:
        return {'kind': 'TypedFunctionTypeNode', 'type': self.type.toJson(), 'argumentType': self.argumentType.toJson(), 'resultType': self.resultType.toJson()}

class ASTTypedFunctionalNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, arguments: list[ASTTypedArgumentNode], captureBindings: list[SymbolCaptureBinding], body: ASTTypedNode, callingConvention: Symbol | None = None) -> None:
        super().__init__(sourcePosition, type)
        self.arguments = arguments
        self.captureBindings = captureBindings
        self.body = body
        self.callingConvention = callingConvention

    def isTypedFunctionalNode(self) -> bool:
        return True

class ASTTypedIfNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, condition: ASTTypedNode, trueExpression: ASTTypedNode, falseExpression: ASTTypedNode) -> None:
        super().__init__(sourcePosition, type)
        self.condition = condition
        self.trueExpression = trueExpression
        self.falseExpression = falseExpression
    
    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedIfNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'TypedIf', 'type': self.type.toJson(), 'condition': self.condition.toJson(), 'trueExpression' : self.trueExpression.toJson(), 'falseExpression' : self.falseExpression.toJson()}

class ASTTypedBreakNode(ASTTypedNode):
    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedBreakNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedBreak', 'type': self.type.toJson()}

class ASTTypedContinueNode(ASTTypedNode):
    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedContinueNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedContinue', 'type': self.type.toJson()}

class ASTTypedDoWhileNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, bodyExpression: ASTNode, condition: ASTNode, continueExpression: ASTNode) -> None:
        super().__init__(sourcePosition, type)
        self.bodyExpression = bodyExpression
        self.condition = condition
        self.continueExpression = continueExpression
    
    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedDoWhileNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'TypedDoWhile', 'type': self.type.toJson(), 'bodyExpression' : optionalASTNodeToJson(self.bodyExpression), 'condition': optionalASTNodeToJson(self.condition.toJson()), 'continueExpression' : optionalASTNodeToJson(self.continueExpression)}

class ASTTypedWhileNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, condition: ASTNode, bodyExpression: ASTNode, continueExpression: ASTNode) -> None:
        super().__init__(sourcePosition, type)
        self.condition = condition
        self.bodyExpression = bodyExpression
        self.continueExpression = continueExpression
    
    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedWhileNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'TypedWhile', 'type': self.type.toJson(), 'condition': optionalASTNodeToJson(self.condition.toJson()), 'bodyExpression' : optionalASTNodeToJson(self.bodyExpression), 'continueExpression' : optionalASTNodeToJson(self.continueExpression)}

class ASTTypedPiNode(ASTTypedFunctionalNode):
    def isTypedPiNode(self) -> bool:
        return True

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedPiNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedPi', 'type': self.type.toJson(), 'arguments': list(map(lambda n: n.toJson(), self.arguments)), 'body': self.body.toJson(), 'callingConvention': optionalToJson(self.callingConvention)}

class ASTTypedSigmaNode(ASTTypedFunctionalNode):
    def isTypedSigmaNode(self) -> bool:
        return True

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedSigmaNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedSigma', 'type': self.type.toJson(), 'arguments': list(map(lambda n: n.toJson(), self.arguments)), 'body': self.body.toJson()}

class ASTTypedLambdaNode(ASTTypedFunctionalNode):
    def isTypedLambdaNode(self) -> bool:
        return True

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedLambdaNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedLambda', 'type': self.type.toJson(), 'arguments': list(map(lambda n: n.toJson(), self.arguments)), 'body': self.body.toJson(), 'callingConvention': optionalToJson(self.callingConvention)}

class ASTTypedBindingDefinitionNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, binding: SymbolLocalBinding, valueExpression: ASTNode, isMutable = False, isPublic = False, module: Module = None) -> None:
        super().__init__(sourcePosition, type)
        self.binding = binding
        self.valueExpression = valueExpression
        self.isMutable = isMutable
        self.isPublic = isPublic
        self.module = module

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedBindingDefinitionNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedBindingDefinitionNode', 'binding': self.binding.toJson(), 'valueExpression': self.valueExpression.toJson()}


class ASTTypedOverloadsNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, alternatives: list[ASTNode]) -> None:
        super().__init__(sourcePosition, type)
        self.alternatives = alternatives

    def isTypedOverloadsNode(self) -> bool:
        return True

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedOverloadsNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedOverloads', 'type': self.type.toJson(), 'alternatives': list(map(optionalASTNodeToJson, self.alternatives))}
    
class ASTTypedSequenceNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, elements: list[ASTTypedNode]) -> None:
        super().__init__(sourcePosition, type)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedSequenceNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedSequence', 'type': self.type.toJson(), 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTTypedTupleNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition, type)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedTupleNode(self)

    def isTypedTupleNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'TypedTuple', 'type': self.type.toJson(), 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTTypedTupleAtNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, tuple: ASTNode, index: int) -> None:
        super().__init__(sourcePosition, type)
        self.tuple = tuple
        self.index = index

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedTupleAtNode(self)

    def isTypedTupleAtNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'TypedTupleAt', 'type': self.type.toJson(), 'tuple': self.tuple.toJson(), 'index': self.index}

class ASTTypedFromModuleImportNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, module: ASTTypedNode, name: Symbol) -> None:
        super().__init__(sourcePosition, type)
        self.module = module
        self.name = name
    
    def accept(self, visitor):
        return visitor.visitTypedFromModuleImportNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedFromModuleImport', 'type': self.type.toJson(), 'module': self.module.toJson(), 'name': self.name.toJson()}

class ASTTypedFromExternalImportWithTypeNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, externalName: Symbol, name: Symbol) -> None:
        super().__init__(sourcePosition, type)
        self.externalName = externalName
        self.name = name
    
    def accept(self, visitor):
        return visitor.visitTypedFromExternalImportWithTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedFromExternalImport', 'type': self.type.toJson(), 'externalName': self.externalName.toJson(), 'name': self.name.toJson()}


class ASTTypedModuleExportValueNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, externalName: Symbol | None, name: Symbol, value: ASTTypeNode | ASTTypedNode, module: Module) -> None:
        super().__init__(sourcePosition, type)
        self.externalName = externalName
        self.name = name
        self.value = value
        self.module = module
    
    def accept(self, visitor):
        return visitor.visitTypedModuleExportValueNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedModuleExport', 'type': self.type.toJson(), 'externalName': optionalToJson(self.externalName), 'name': self.name.toJson(), 'value:' : self.value.toJson()}

class ASTTypedModuleEntryPointNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, entryPoint: ASTTypedNode, module: Module) -> None:
        super().__init__(sourcePosition, type)
        self.entryPoint = entryPoint
        self.module = module
    
    def accept(self, visitor):
        return visitor.visitTypedModuleEntryPointNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedModuleEntryPoint', 'type': self.type.toJson(), 'entryPoint': self.entryPoint.toJson()}
    
def optionalASTNodeToJson(node: ASTNode | None) -> dict | None:
    if node is None:
        return None
    else:
        return node.toJson()

class ASTSequentialVisitor(ASTVisitor):
    def visitNode(self, node: ASTNode):
        return node.accept(self)

    def visitOptionalNode(self, node: ASTNode):
        if node is not None:
            self.visitNode(node)

    def visitApplicationNode(self, node: ASTApplicationNode):
        self.visitNode(node.functional)
        for arg in node.arguments:
            self.visitNode(arg)

    def visitAllocaMutableWithValueNode(self, node: ASTAllocaMutableWithValueNode):
        self.visitNode(node.initialValue)

    def visitArgumentApplicationNode(self, node: ASTArgumentApplicationNode):
        self.visitNode(node.functional)
        self.visitNode(node.argument)
    
    def visitArgumentNode(self, node: ASTArgumentNode):
        self.visitOptionalNode(node.nameExpression)
        self.visitOptionalNode(node.typeExpression)

    def visitBinaryExpressionSequenceNode(self, node: ASTBinaryExpressionSequenceNode):
        for element in node.elements:
            self.visitNode(element)

    def visitErrorNode(self, node: ASTErrorNode):
        pass

    def visitFunctionTypeNode(self, node: ASTFunctionTypeNode):
        self.visitNode(node.argumentType)
        self.visitNode(node.resultType)

    def visitFunctionalDependentTypeNode(self, node: ASTFunctionalDependentTypeNode):
        for arg in node.arguments:
            self.visitNode(arg)
        self.visitOptionalNode(node.resultType)

    def visitIdentifierReferenceNode(self, node: ASTIdentifierReferenceNode):
        pass

    def visitIfNode(self, node: ASTIfNode):
        self.visitNode(node.condition)
        if node.trueExpression is not None:
            self.visitNode(node.trueExpression)
        if node.falseExpression is not None:
            self.visitNode(node.falseExpression)

    def visitBreakNode(self, node: ASTBreakNode):
        pass

    def visitContinueNode(self, node: ASTContinueNode):
        pass

    def visitDoWhileNode(self, node: ASTDoWhileNode):
        if node.bodyExpression is not None:
            self.visitNode(node.bodyExpression)
        if node.condition is not None:
            self.visitNode(node.condition)
        if node.continueExpression is not None:
            self.visitNode(node.continueExpression)

    def visitWhileNode(self, node: ASTWhileNode):
        if node.condition is not None:
            self.visitNode(node.condition)
        if node.bodyExpression is not None:
            self.visitNode(node.bodyExpression)
        if node.continueExpression is not None:
            self.visitNode(node.continueExpression)

    def visitLexicalBlockNode(self, node: ASTLexicalBlockNode):
        self.visitNode(node.expression)

    def visitPiNode(self, node: ASTPiNode):
        self.visitOptionalNode(node.argumentType)
        self.visitOptionalNode(node.argumentName)
        self.visitNode(node.body)

    def visitSigmaNode(self, node: ASTSigmaNode):
        self.visitOptionalNode(node.argumentType)
        self.visitOptionalNode(node.argumentName)
        self.visitNode(node.body)

    def visitFunctionNode(self, node: ASTFunctionNode):
        self.visitNode(node.functionalType)
        self.visitNode(node.body)

    def visitLambdaNode(self, node: ASTLambdaNode):
        self.visitOptionalNode(node.argumentType)
        self.visitOptionalNode(node.argumentName)
        self.visitNode(node.body)

    def visitLiteralNode(self, node):
        pass

    def visitLiteralTypeNode(self, node):
        pass

    def visitBindingDefinitionNode(self, node: ASTBindingDefinitionNode):
        self.visitOptionalNode(node.nameExpression)
        self.visitOptionalNode(node.expectedTypeExpression)
        self.visitOptionalNode(node.initialValueExpression)

    def visitMessageSendNode(self, node: ASTMessageSendNode):
        self.visitOptionalNode(node.receiver)
        self.visitNode(node.selector)
        for arg in node.arguments:
            self.visitNode(arg)

    def visitOverloadsNode(self, node: ASTOverloadsNode):
        for alternative in node.alternatives:
            self.visitNode(alternative)

    def visitSequenceNode(self, node: ASTSequenceNode):
        for expression in node.elements:
            self.visitNode(expression)

    def visitTupleNode(self, node: ASTTupleNode):
        for expression in node.elements:
            self.visitNode(expression)

    def visitOverloadsTypeNode(self, node: ASTOverloadsTypeNode):
        for expression in node.alternativeTypes:
            self.visitNode(expression)

    def visitProductTypeNode(self, node: ASTProductTypeNode):
        for expression in node.elementTypes:
            self.visitNode(expression)

    def visitSumTypeNode(self, node: ASTSumTypeNode):
        for expression in node.alternativeTypes:
            self.visitNode(expression)

    def visitImportModuleNode(self, node: ASTImportModuleNode):
        self.visitNode(node.name)
    
    def visitFromModuleImportWithTypeNode(self, node: ASTFromModuleImportWithTypeNode):
        self.visitNode(node.module)
        self.visitNode(node.name)
        self.visitNode(node.type)

    def visitFromExternalImportWithTypeNode(self, node: ASTFromExternalImportWithTypeNode):
        self.visitNode(node.externalName)
        self.visitNode(node.name)
        self.visitNode(node.type)

    def visitModuleExportValueNode(self, node: ASTModuleExportValueNode):
        self.visitNode(node.name)
        self.visitNode(node.value)

    def visitModuleEntryPointNode(self, node: ASTModuleEntryPointNode):
        self.visitNode(node.entryPoint)

    def visitTypedAllocaMutableWithValueNode(self, node: ASTTypedAllocaMutableWithValueNode):
        self.visitNode(node.type)
        self.visitNode(node.initialValue)

    def visitTypedArgumentNode(self, node: ASTTypedArgumentNode):
        self.visitNode(node.type)

    def visitTypedApplicationNode(self, node: ASTTypedApplicationNode):
        for binding, substitution in node.implicitValueSubstitutions:
            self.visitNode(substitution)

        self.visitNode(node.functional)
        self.visitNode(node.argument)

    def visitTypedFunctionTypeNode(self, node: ASTTypedFunctionTypeNode):
        self.visitNode(node.argumentType)
        self.visitNode(node.resultType)

    def visitTypedPiNode(self, node: ASTTypedPiNode):
        self.visitNode(node.type)
        for argument in node.arguments:
            self.visitNode(argument)
        self.visitNode(node.body)

    def visitTypedSigmaNode(self, node: ASTTypedSigmaNode):
        self.visitNode(node.type)
        for argument in node.arguments:
            self.visitNode(argument)
        self.visitNode(node.body)

    def visitTypedErrorNode(self, node: ASTTypedErrorNode):
        return node
    
    def visitTypedIdentifierReferenceNode(self, node: ASTTypedIdentifierReferenceNode):
        self.visitNode(node.type)

    def visitTypedIfNode(self, node: ASTTypedIfNode):
        self.visitNode(node.type)
        self.visitNode(node.condition)
        self.visitNode(node.trueExpression)
        self.visitNode(node.falseExpression)

    def visitTypedBreakNode(self, node: ASTTypedBreakNode):
        pass

    def visitTypedContinueNode(self, node: ASTTypedContinueNode):
        pass

    def visitTypedDoWhileNode(self, node: ASTTypedDoWhileNode):
        self.visitNode(node.type)
        self.visitNode(node.bodyExpression)
        self.visitNode(node.condition)
        self.visitNode(node.continueExpression)

    def visitTypedWhileNode(self, node: ASTTypedWhileNode):
        self.visitNode(node.type)
        self.visitNode(node.condition)
        self.visitNode(node.bodyExpression)
        self.visitNode(node.continueExpression)

    def visitTypedLambdaNode(self, node: ASTTypedLambdaNode):
        self.visitNode(node.type)
        for argument in node.arguments:
            self.visitNode(argument)
        self.visitNode(node.body)

    def visitTypedLiteralNode(self, node: ASTTypedLiteralNode):
        self.visitNode(node.type)

    def visitTypedBindingDefinitionNode(self, node: ASTTypedBindingDefinitionNode):
        self.visitNode(node.valueExpression)

    def visitTypedOverloadedApplicationNode(self, node: ASTTypedOverloadedApplicationNode):
        for alternativeImplicitValueSubstitutions in node.alternativeImplicitValueSubstitutions:
            for binding, substitution in alternativeImplicitValueSubstitutions:
                self.visitNode(substitution)

        self.visitNode(node.overloads)
        self.visitNode(node.argument)
        self.visitNode(node.type)

    def visitTypedOverloadsNode(self, node: ASTTypedOverloadsNode):
        self.visitNode(node.type)
        for alternatives in node.alternatives:
            self.visitNode(alternatives)

    def visitTypedSequenceNode(self, node: ASTSequenceNode):
        self.visitNode(node.type)
        for expression in node.elements:
            self.visitNode(expression)

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        self.visitNode(node.type)
        for expression in node.elements:
            self.visitNode(expression)

    def visitTypedTupleAtNode(self, node: ASTTypedTupleAtNode):
        self.visitNode(node.type)
        self.visitNode(node.tuple)

    def visitTypedFromModuleImportNode(self, node: ASTTypedFromModuleImportNode):
        self.visitNode(node.type)
        self.visitNode(node.module)

    def visitTypedFromExternalImportWithTypeNode(self, node):
        self.visitNode(node.type)

    def visitTypedModuleExportValueNode(self, node: ASTTypedModuleExportValueNode):
        self.visitNode(node.value)

    def visitTypedModuleEntryPointNode(self, node: ASTTypedModuleEntryPointNode):
        self.visitNode(node.entryPoint)

class ASTErrorVisitor(ASTSequentialVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.errorNodes = []
    
    def visitErrorNode(self, node: ASTErrorNode):
        self.errorNodes.append(node)

    def visitTypedErrorNode(self, node: ASTTypedErrorNode):
        self.errorNodes.append(node)

    def checkASTAndPrintErrors(self, node: ASTNode):
        self.visitNode(node)
        for errorNode in self.errorNodes:
            print('%s: %s' % (str(errorNode.sourcePosition), errorNode.message))
        return len(self.errorNodes) == 0

class ASTTypecheckedVisitor(ASTVisitor):
    def visitApplicationNode(self, node):
        assert False

    def visitAllocaMutableWithValueNode(self, node):
        assert False

    def visitArgumentNode(self, node):
        assert False

    def visitArgumentApplicationNode(self, node: ASTArgumentApplicationNode):
        assert False

    def visitBinaryExpressionSequenceNode(self, node):
        assert False

    def visitErrorNode(self, node):
        assert False

    def visitPiNode(self, node):
        assert False

    def visitSigmaNode(self, node):
        assert False

    def visitFunctionNode(self, node):
        assert False

    def visitFunctionTypeNode(self, node):
        assert False

    def visitFunctionalDependentTypeNode(self, node):
        assert False

    def visitIdentifierReferenceNode(self, node):
        assert False

    def visitIfNode(self, node):
        assert False

    def visitBreakNode(self, node):
        assert False

    def visitContinueNode(self, node):
        assert False

    def visitDoWhileNode(self, node):
        assert False

    def visitWhileNode(self, node):
        assert False

    def visitLambdaNode(self, node):
        assert False

    def visitLexicalBlockNode(self, node):
        assert False

    def visitLiteralNode(self, node):
        assert False

    def visitBindingDefinitionNode(self, node):
        assert False

    def visitMessageSendNode(self, node):
        assert False

    def visitImportModuleNode(self, node: ASTImportModuleNode):
        assert False
    
    def visitFromModuleImportWithTypeNode(self, node: ASTFromModuleImportWithTypeNode):
        assert False

    def visitFromExternalImportWithTypeNode(self, node: ASTFromExternalImportWithTypeNode):
        assert False

    def visitModuleExportValueNode(self, node: ASTModuleExportValueNode):
        assert False

    def visitModuleEntryPointNode(self, node):
        assert False

    def visitOverloadsNode(self, node):
        assert False

    def visitSequenceNode(self, node):
        assert False

    def visitTupleNode(self, node):
        assert False
