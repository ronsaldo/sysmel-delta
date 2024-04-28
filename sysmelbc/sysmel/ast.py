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
    def visitBindableNameNode(self, node):
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
    def visitFormDecoratedTypeNode(self, node):
        pass

    @abstractmethod
    def visitFormArrayTypeNode(self, node):
        pass

    @abstractmethod
    def visitFormPointerTypeNode(self, node):
        pass

    @abstractmethod
    def visitFormReferenceTypeNode(self, node):
        pass

    @abstractmethod
    def visitFormTemporaryReferenceTypeNode(self, node):
        pass

    @abstractmethod
    def visitFormDictionaryTypeNode(self, node):
        pass

    @abstractmethod
    def visitFormProductTypeNode(self, node):
        pass

    @abstractmethod
    def visitFormRecordTypeNode(self, node):
        pass

    @abstractmethod
    def visitFormSumTypeNode(self, node):
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
    def visitArraySubscriptAtNode(self, node):
        pass

    @abstractmethod
    def visitPointerLikeLoadNode(self, node):
        pass

    @abstractmethod
    def visitPointerLikeStoreNode(self, node):
        pass

    @abstractmethod
    def visitPointerLikeReinterpretToNode(self, node):
        pass

    @abstractmethod
    def visitPointerLikeSubscriptAtNode(self, node):
        pass

    @abstractmethod
    def visitOverloadsTypeNode(self, node):
        pass

    @abstractmethod
    def visitDecoratedTypeNode(self, node):
        pass

    @abstractmethod
    def visitPointerTypeNode(self, node):
        pass

    @abstractmethod
    def visitReferenceTypeNode(self, node):
        pass

    @abstractmethod
    def visitTemporaryReferenceTypeNode(self, node):
        pass

    @abstractmethod
    def visitArrayTypeNode(self, node):
        pass

    @abstractmethod
    def visitDictionaryTypeNode(self, node):
        pass

    @abstractmethod
    def visitProductTypeNode(self, node):
        pass

    @abstractmethod
    def visitRecordTypeNode(self, node):
        pass

    @abstractmethod
    def visitSumTypeNode(self, node):
        pass

    @abstractmethod
    def visitDictionaryNode(self, node):
        pass

    @abstractmethod
    def visitSequenceNode(self, node):
        pass

    @abstractmethod
    def visitRecordNode(self, node):
        pass

    @abstractmethod
    def visitModifiedRecordNode(self, node):
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
    def visitTypedArraySubscriptAtNode(self, node):
        pass

    @abstractmethod
    def visitTypedPointerLikeLoadNode(self, node):
        pass

    @abstractmethod
    def visitTypedPointerLikeStoreNode(self, node):
        pass

    @abstractmethod
    def visitTypedPointerLikeReinterpretToNode(self, node):
        pass

    @abstractmethod
    def visitTypedPointerLikeSubscriptAtNode(self, node):
        pass

    @abstractmethod
    def visitTypedSequenceNode(self, node):
        pass

    @abstractmethod
    def visitTypedDictionaryNode(self, node):
        pass

    @abstractmethod
    def visitTypedTupleNode(self, node):
        pass

    @abstractmethod
    def visitTypedModifiedTupleNode(self, node):
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

class ASTBindableNameNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, typeExpression: ASTNode, nameExpression: ASTNode, isImplicit: bool = False, isExistential: bool = False, isVariadic: bool = False) -> None:
        super().__init__(sourcePosition)
        self.typeExpression = typeExpression
        self.nameExpression = nameExpression
        self.isImplicit = isImplicit
        self.isExistential = isExistential
        self.isVariadic = isVariadic

    def isBindableNameNode(self) -> bool:
        return True
    
    def parseAndUnpackArgumentsPattern(self):
        return [self], self.isExistential, self.isVariadic

    def accept(self, visitor: ASTVisitor):
        return visitor.visitBindableNameNode(self)

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
    ByteArrayStart = 3
    Block = 4
    Dictionary = 5

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
    def __init__(self, sourcePosition: SourcePosition, argumentPattern: ASTNode, resultType: ASTNode, callingConvention: Symbol) -> None:
        super().__init__(sourcePosition)
        self.argumentPattern = argumentPattern
        self.resultType = resultType
        self.callingConvention = callingConvention

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFunctionalDependentTypeNode(self)
    
    def isFunctionalDependentTypeNode(self) -> bool:
        return True

    def withCallingConventionNamed(self, callingConventionName: TypedValue):
        if callingConventionName == self.callingConvention:
            return self
        return ASTFunctionalDependentTypeNode(self.sourcePosition, self.argumentPattern, self.resultType, callingConventionName)
    
    def constructLambdaWithBody(self, body):
        bodyOrInnerLambda = body
        if self.resultType.isFunctionalDependentTypeNode():
            bodyOrInnerLambda = self.resultType.constructLambdaWithBody(body)
        argumentNodes, isExistential, isVariadic = self.argumentPattern.parseAndUnpackArgumentsPattern()
        return ASTLambdaNode(self.sourcePosition, argumentNodes, isVariadic, self.resultType, bodyOrInnerLambda, self.callingConvention)
    
    def toJson(self) -> dict:
        return {'kind': 'FunctionalType', 'argumentPattern': list(map(optionalASTNodeToJson, self.argumentPattern)), 'resultType': optionalASTNodeToJson(self.resultType)}

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

class ASTFormDerivedTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, baseType: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.baseType = baseType

class ASTFormDecoratedTypeNode(ASTFormDerivedTypeNode):
    def __init__(self, sourcePosition: SourcePosition, baseType: ASTNode, decorations: int):
        super().__init__(sourcePosition, baseType)
        self.decorations = decorations
        
    def accept(self, visitor: ASTVisitor):
        return visitor.visitFormDecoratedTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'FormDecoratedType', 'baseType': self.baseType.toJson(), 'decorations' : self.decorations}

class ASTFormArrayTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, elementType: ASTNode, size: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.elementType = elementType
        self.size = size

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFormArrayTypeNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'FormArrayTypeNode', 'elementType': self.elementType.toJson(), 'size': self.size.toJson()}
    
class ASTFormPointerTypeNode(ASTFormDerivedTypeNode):
    def accept(self, visitor: ASTVisitor):
        return visitor.visitFormPointerTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'FormPointerType', 'baseType': self.baseType.toJson()}

class ASTFormReferenceTypeNode(ASTFormDerivedTypeNode):
    def accept(self, visitor: ASTVisitor):
        return visitor.visitFormReferenceTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'FormReferenceType', 'baseType': self.baseType.toJson()}

class ASTFormTemporaryReferenceTypeNode(ASTFormDerivedTypeNode):
    def accept(self, visitor: ASTVisitor):
        return visitor.visitFormTemporaryReferenceTypeNode(self)

    def toJson(self) -> dict:
        return {'kind': 'FormTemporaryReferenceType', 'baseType': self.baseType.toJson()}
    
class ASTFormDictionaryTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, keyType: ASTNode, valueType: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.keyType = keyType
        self.valueType = valueType

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFormDictionaryTypeNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'FormDictionaryType', 'key' : self.keyType.toJson(), 'value' : self.valueType.toJson()}
    
class ASTFormProductTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFormProductTypeNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'FormProductType', 'elements': list(map(lambda n: n.toJson(), self.elements))}

class ASTFormRecordTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, name: ASTNode, fieldNames: list[ASTNode], fieldTypes: list[ASTNode], isRecursive: bool = False) -> None:
        super().__init__(sourcePosition)
        self.name = name
        self.fieldNames = fieldNames
        self.fieldTypes = fieldTypes
        self.isRecursive = isRecursive

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFormRecordTypeNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'FormRecordType', 'name' : optionalASTNodeToJson(self.name), 'fieldNames': list(map(lambda n: n.toJson(), self.fieldNames)), 'fieldTypes': list(map(lambda n: n.toJson(), self.fieldTypes))}
    
class ASTFormSumTypeNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, name: ASTNode, elements: list[ASTNode], isRecursive: bool = False) -> None:
        super().__init__(sourcePosition)
        self.name = name
        self.elements = elements
        self.isRecursive = isRecursive

    def accept(self, visitor: ASTVisitor):
        return visitor.visitFormSumTypeNode(self)
    
    def toJson(self) -> dict:
        return {'kind': 'FormSumType', 'elements': list(map(lambda n: n.toJson(), self.elements))}

class ASTPiNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, arguments: list[ASTNode], isVariadic: bool, body: ASTNode, callingConvention: Symbol) -> None:
        super().__init__(sourcePosition)
        self.arguments = arguments
        self.isVariadic = isVariadic
        self.body = body
        self.callingConvention = callingConvention

    def accept(self, visitor: ASTVisitor):
        return visitor.visitPiNode(self)

    def toJson(self) -> dict:
        return {'kind': 'PiNode', 'arguments': list(map(lambda x: x.toJson(), self.arguments)), 'isVariadic': self.isVariadic, 'body': optionalASTNodeToJson(self.body)}

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
    def __init__(self, sourcePosition: SourcePosition, arguments: list[ASTBindableNameNode], isVariadic: bool, resultType: ASTNode, body: ASTNode, callingConvention: Symbol = None) -> None:
        super().__init__(sourcePosition)
        self.arguments = arguments
        self.isVariadic = isVariadic
        self.resultType = resultType
        self.body = body
        self.callingConvention = callingConvention

    def accept(self, visitor: ASTVisitor):
        return visitor.visitLambdaNode(self)

    def toJson(self) -> dict:
        return {'kind': 'Lambda', 'arguments': list(map(lambda x: x.toJson(), self.arguments)), 'resultType': optionalASTNodeToJson(self.resultType), 'body': self.body.toJson(), 'callingConvention' : optionalToJson(self.callingConvention)}

class ASTBindingDefinitionNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, nameExpression: ASTNode, expectedTypeExpression: ASTNode, initialValueExpression: ASTNode, isMutable = False, isPublic = False) -> None:
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
    
    def attemptToUnpackTupleExpressionsAt(self, sourcePosition):
        return self.value.attemptToUnpackTupleExpressionsAt(sourcePosition)

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

class ASTDictionaryNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitDictionaryNode(self)
    
    def isDictionaryNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'Dictionary', 'elements': list(map(optionalASTNodeToJson, self.elements))}

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

    def attemptToUnpackTupleExpressionsAt(self, sourcePosition):
        return self.elements

    def parseAndUnpackArgumentsPattern(self):
        isExistential = False
        isVariadic = False
        if len(self.elements) == 1 and self.elements[0].isBindableNameNode():
            isExistential = self.elements[0].isExistential
        if len(self.elements) > 0 and self.elements[-1].isBindableNameNode():
            isVariadic = self.elements[-1].isVariadic
        return self.elements, isExistential, isVariadic
    
    def toJson(self) -> dict:
        return {'kind': 'Tuple', 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTRecordNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, fieldNames: list[ASTNode], fieldValues: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.type = type
        self.fieldNames = fieldNames
        self.fieldValues = fieldValues

    def accept(self, visitor: ASTVisitor):
        return visitor.visitRecordNode(self)
    
    def isRecordNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'record', 'type': self.type.toJson(), 'fieldNames': list(map(optionalASTNodeToJson, self.fieldNames)), 'fieldValues': list(map(optionalASTNodeToJson, self.fieldValues))}

class ASTModifiedRecordNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, record: ASTNode, fieldNames: list[ASTNode], fieldValues: list[ASTNode]) -> None:
        super().__init__(sourcePosition)
        self.record = record
        self.fieldNames = fieldNames
        self.fieldValues = fieldValues

    def accept(self, visitor: ASTVisitor):
        return visitor.visitModifiedRecordNode(self)
    
    def isRecordNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'modifiedRecord', 'record': self.record.toJson(), 'fieldNames': list(map(optionalASTNodeToJson, self.fieldNames)), 'fieldValues': list(map(optionalASTNodeToJson, self.fieldValues))}

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

class ASTDerivedTypeNode(ASTTypeNode):
    def __init__(self, sourcePosition: SourcePosition, baseType: ASTTypeNode) -> None:
        super().__init__(sourcePosition)
        self.baseType = baseType

    def getBaseTypeExpressionAt(self, sourcePosition: SourcePosition) -> ASTTypeNode:
        return self.baseType

    def isCVarArgCompatibleTypeNode(self) -> bool:
        return self.baseType.isCVarArgCompatibleTypeNode()

    def computeTypeUniverseIndex(self) -> int:
        return self.baseType.computeTypeUniverseIndex()

class ASTDecoratedTypeNode(ASTDerivedTypeNode):
    def __init__(self, sourcePosition: SourcePosition, baseType: ASTTypeNode, decorations: int) -> None:
        super().__init__(sourcePosition, baseType)
        self.decorations = decorations

    def accept(self, visitor):
        return visitor.visitDecoratedTypeNode(self)
    
    def prettyPrint(self) -> str:
        result = self.baseType.prettyPrint()
        if self.isMutable():
            result += ' mutable'
        if self.isVolatile():
            result += ' volatile'
        return result

    def isDecoratedTypeNode(self) -> bool:
        return True

    def isMutable(self) -> bool:
        return (self.decorations & DecoratedType.Mutable) != 0

    def isVolatile(self) -> bool:
        return (self.decorations & DecoratedType.Volatile) != 0
    
    def toJson(self) -> dict:
        return {'kind': 'DecoratedType', 'baseType': self.baseType.toJson(), 'decorations': self.decorations}

class ASTPointerTypeNode(ASTDerivedTypeNode):
    def accept(self, visitor):
        return visitor.visitPointerTypeNode(self)

    def prettyPrint(self) -> str:
        return self.baseType.prettyPrint() + ' pointer'
    
    def isPointerTypeNode(self) -> bool:
        return True

    def isPointerTypeNodeOrLiteral(self) -> bool:
        return True
    
    def isCVarArgCompatibleTypeNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'PointerType', 'baseType': self.baseType.toJson()}

class ASTReferenceTypeNode(ASTDerivedTypeNode):
    def accept(self, visitor):
        return visitor.visitReferenceType(self)

    def prettyPrint(self) -> str:
        return self.baseType.prettyPrint() + ' ref'

    def isReferenceTypeNode(self) -> bool:
        return True
    
    def isReferenceLikeTypeNodeOrLiteral(self) -> bool:
        return True

    def getElementTypeExpressionAt(self, sourcePosition: SourcePosition) -> ASTTypeNode:
        return self.baseType.getElementTypeExpressionAt(sourcePosition)

    def toJson(self) -> dict:
        return {'kind': 'ReferenceType', 'baseType': self.baseType.toJson()}

class ASTTemporaryReferenceTypeNode(ASTDerivedTypeNode):
    def accept(self, visitor):
        return visitor.visitTemporaryReferenceType(self)

    def prettyPrint(self) -> str:
        return self.baseType.prettyPrint() + ' tempRef'

    def isTemporaryReferenceTypeNode(self) -> bool:
        return True

    def isReferenceLikeTypeNodeOrLiteral(self) -> bool:
        return True
    
    def getElementTypeExpressionAt(self, sourcePosition: SourcePosition) -> ASTTypeNode:
        return self.baseType.getElementTypeExpressionAt(sourcePosition)

    def toJson(self) -> dict:
        return {'kind': 'TemporaryReferenceType', 'baseType': self.baseType.toJson()}

class ASTArrayTypeNode(ASTTypeNode):
    def __init__(self, sourcePosition: SourcePosition, elementType: ASTTypeNode, size: ASTTypedNode) -> None:
        super().__init__(sourcePosition)
        self.elementType = elementType
        self.size = size

    def computeTypeUniverseIndex(self) -> int:
        return self.elementType.computeTypeUniverseIndex()
    
    def accept(self, visitor):
        return visitor.visitArrayTypeNode(self)

    def getElementTypeExpressionAt(self, sourcePosition: SourcePosition) -> ASTTypeNode:
        return self.elementType
    
    def prettyPrint(self) -> str:
        return self.elementType.prettyPrint() + '[' + self.size.prettyPrint() + ']'
    
    def isArrayTypeNode(self) -> bool:
        return True

    def isArrayTypeNodeOrLiteral(self) -> bool:
        return True
    
    def toJson(self) -> dict:
        return {'kind': 'ArrayType', 'elementType': self.elementType.toJson(), 'size' : self.size.toJson()}

class ASTDictionaryTypeNode(ASTTypeNode):
    def __init__(self, sourcePosition: SourcePosition, keyType: ASTTypeNode, valueType: ASTTypeNode) -> None:
        super().__init__(sourcePosition)
        self.keyType = keyType
        self.valueType = valueType
        self.typeUniverseIndex = None

    def computeTypeUniverseIndex(self) -> int:
        if self.typeUniverseIndex is None:
            self.typeUniverseIndex = max(self.keyType.computeTypeUniverseIndex(), self.valueType.computeTypeUniverseIndex())
        
        return self.typeUniverseIndex
    
    def accept(self, visitor):
        return visitor.visitDictionaryTypeNode(self)

    def isDictionaryTypeNodeOrLiteral(self) -> bool:
        return True

    def isDictionaryTypeNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'DictionaryType', 'key': self.keyType.toJson(), 'value': self.valueType.toJson()}
    
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
    
    def asUnpackedTupleTypeExpressionsAt(self, sourcePosition: SourcePosition):
        return self

    def isProductTypeNodeOrLiteral(self) -> bool:
        return True

    def isProductTypeNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'ProductType', 'elementTypes': list(map(optionalASTNodeToJson, self.elementTypes))}
    
class ASTRecordTypeNode(ASTProductTypeNode):
    def __init__(self, sourcePosition: SourcePosition, name: Symbol, elementTypes: list[ASTTypeNode], fieldNames: list[Symbol], isRecursive: bool) -> None:
        super().__init__(sourcePosition, elementTypes)
        self.name = name
        self.fieldNames = fieldNames
        self.isRecursive = isRecursive
    
    def accept(self, visitor):
        return visitor.visitRecordTypeNode(self)
    
    def asUnpackedTupleTypeExpressionsAt(self, sourcePosition: SourcePosition):
        return self

    def isRecordTypeNodeOrLiteral(self) -> bool:
        return True

    def isRecordTypeNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'RecordType', 'name' : optionalToJson(self.name), 'elementTypes': list(map(optionalASTNodeToJson, self.elementTypes)), 'fieldNames': list(map(optionalToJson, self.fieldNames))}
    
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

    def isSumTypeNode(self) -> bool:
        return True

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
    def __init__(self, sourcePosition: SourcePosition, externalName: ASTNode, name: ASTNode, value: ASTNode) -> None:
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

class ASTArraySubscriptAtNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, array: ASTNode, index: ASTNode, resultAsReference: bool) -> None:
        super().__init__(sourcePosition)
        self.array = array
        self.index = index
        self.resultAsReference = resultAsReference
    
    def accept(self, visitor):
        return visitor.visitArraySubscriptAtNode(self)

    def toJson(self) -> dict:
        return {'kind': 'ArraySubscriptAt', 'array': self.array.toJson(), 'index': self.index.toJson(), 'resultAsReference': self.resultAsReference}

class ASTPointerLikeLoadNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, pointer: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.pointer = pointer
    
    def accept(self, visitor):
        return visitor.visitPointerLikeLoadNode(self)

    def toJson(self) -> dict:
        return {'kind': 'PointerLikeLoad', 'pointer': self.pointer.toJson()}

class ASTPointerLikeStoreNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, pointer: ASTNode, value: ASTNode, returnPointer: bool) -> None:
        super().__init__(sourcePosition)
        self.pointer = pointer
        self.value = value
        self.returnPointer = returnPointer
    
    def accept(self, visitor):
        return visitor.visitPointerLikeStoreNode(self)

    def toJson(self) -> dict:
        return {'kind': 'PointerLikeStore', 'pointer': self.pointer.toJson(), 'returnPointer': self.returnPointer}

class ASTPointerLikeReinterpretToNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, pointer: ASTNode, targetType: ASTNode) -> None:
        super().__init__(sourcePosition)
        self.pointer = pointer
        self.targetType = targetType
    
    def accept(self, visitor):
        return visitor.visitPointerLikeReinterpretToNode(self)

    def toJson(self) -> dict:
        return {'kind': 'PointerLikeAsPointer', 'pointer': self.pointer.toJson(), 'targetType' : self.targetType.toJson()}

class ASTPointerLikeSubscriptAtNode(ASTNode):
    def __init__(self, sourcePosition: SourcePosition, pointer: ASTNode, index: ASTNode, resultAsReference: bool) -> None:
        super().__init__(sourcePosition)
        self.pointer = pointer
        self.index = index
        self.resultAsReference = resultAsReference
    
    def accept(self, visitor):
        return visitor.visitPointerLikeSubscriptAtNode(self)

    def toJson(self) -> dict:
        return {'kind': 'PointerLikeSubscriptAt', 'pointer': self.pointer.toJson(), 'index': self.index.toJson(), 'resultAsReference': self.resultAsReference}

class ASTTypedAllocaMutableWithValueNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, valueType: ASTNode, initialValue: ASTNode) -> None:
        super().__init__(sourcePosition, type)
        self.initialValue = initialValue
        self.valueType = valueType

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedAllocaMutableWithValueNode(self)

    def toJson(self) -> dict:
        return {'kind': 'AllocaMutableWithValue', 'type' : self.type.toJson(), 'valueType': self.valueType.toJson(), 'initialValue': self.initialValue.toJson()}
    
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
        return {'kind': 'TypedArgument', 'type': self.type.toJson(), 'name': optionalToJson(self.binding.name), 'isImplicit': self.isImplicit, 'isExistential': self.isExistential}

class ASTTypedApplicationNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, functional: ASTTypedNode, argument: ASTTypedNode, implicitValueSubstitutions: list[tuple[SymbolBinding, ASTNode]]) -> None:
        super().__init__(sourcePosition, type)
        self.functional = functional
        self.argument = argument
        self.implicitValueSubstitutions = implicitValueSubstitutions

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedApplicationNode(self)

    def prettyPrint(self) -> str:
        return self.functional.prettyPrint() + '(' + self.argument.prettyPrint() + ')'
    
    def toJson(self) -> dict:
        return {'kind': 'TypedApplication', 'type': self.type.toJson(), 'functional': self.functional.toJson(), 'argument': self.argument.toJson()}

class ASTTypedOverloadedApplicationNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, overloads: ASTTypedNode, alternativeImplicitValueSubstitutions: list[tuple[SymbolImplicitValueBinding, ASTNode]], alternativeArguments: list[ASTTypedNode], alternativeIndices: list[int]) -> None:
        super().__init__(sourcePosition, type)
        self.overloads = overloads
        self.alternativeImplicitValueSubstitutions = alternativeImplicitValueSubstitutions
        self.alternativeArguments = alternativeArguments
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
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, arguments: list[ASTTypedArgumentNode], isVariadic: bool, captureBindings: list[SymbolCaptureBinding], body: ASTTypedNode, callingConvention: Symbol) -> None:
        super().__init__(sourcePosition, type)
        self.arguments = arguments
        self.isVariadic = isVariadic
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

class ASTTypedArraySubscriptAtNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, array: ASTTypedNode, index: ASTTypedNode, loadResult: bool) -> None:
        super().__init__(sourcePosition, type)
        self.array = array
        self.index = index
        self.loadResult = loadResult

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedArraySubscriptAtNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedArraySubscriptAt', 'type': self.type.toJson(), 'array': self.array.toJson(), 'index': self.index.toJson(), 'loadResult': self.loadResult}

class ASTTypedPointerLikeLoadNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, pointer: ASTTypedNode, isVolatile = False) -> None:
        super().__init__(sourcePosition, type)
        self.pointer = pointer
        self.isVolatile = isVolatile

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedPointerLikeLoadNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedPointerLikeLoad', 'type': self.type.toJson(), 'pointer': self.pointer.toJson()}

class ASTTypedPointerLikeStoreNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, pointer: ASTTypedNode, value: ASTTypedNode, returnPointer, isVolatile = False) -> None:
        super().__init__(sourcePosition, type)
        self.pointer = pointer
        self.value = value
        self.returnPointer = returnPointer
        self.isVolatile = isVolatile

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedPointerLikeStoreNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedPointerLikeStore', 'type': self.type.toJson(), 'pointer': self.pointer.toJson()}
    
class ASTTypedPointerLikeReinterpretToNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, pointer: ASTTypedNode) -> None:
        super().__init__(sourcePosition, type)
        self.pointer = pointer

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedPointerLikeReinterpretToNode(self)
    
    def isTypedPointerLikeReinterpretToNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'TypedPointerLikeReinterpretTo', 'type': self.type.toJson(), 'pointer': self.pointer.toJson()}
    
class ASTTypedPointerLikeSubscriptAtNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, pointer: ASTTypedNode, index: ASTTypedNode) -> None:
        super().__init__(sourcePosition, type)
        self.pointer = pointer
        self.index = index

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedPointerLikeSubscriptAtNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedPointerSubscriptAt', 'type': self.type.toJson(), 'pointer': self.pointer.toJson(), 'index': self.index.toJson()}

class ASTTypedSequenceNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, elements: list[ASTTypedNode]) -> None:
        super().__init__(sourcePosition, type)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedSequenceNode(self)

    def toJson(self) -> dict:
        return {'kind': 'TypedSequence', 'type': self.type.toJson(), 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTTypedDictionaryNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, elements: list[ASTNode]) -> None:
        super().__init__(sourcePosition, type)
        self.elements = elements

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedDictionaryNode(self)

    def isTypedDictionaryNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'TypedDictionary', 'type': self.type.toJson(), 'elements': list(map(optionalASTNodeToJson, self.elements))}
    
class ASTTypedTupleNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, elements: list[ASTNode], isRecord: bool) -> None:
        super().__init__(sourcePosition, type)
        self.elements = elements
        self.isRecord = isRecord

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedTupleNode(self)

    def attemptToUnpackTupleExpressionsAt(self, sourcePosition):
        return self.elements

    def isTypedTupleNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'TypedTuple', 'type': self.type.toJson(), 'elements': list(map(optionalASTNodeToJson, self.elements))}

class ASTTypedModifiedTupleNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, baseTuple: ASTNode, elements: list[ASTNode], elementIndices: list[int], isRecord: bool) -> None:
        super().__init__(sourcePosition, type)
        self.baseTuple = baseTuple
        self.elements = elements
        self.elementIndices = elementIndices
        self.isRecord = isRecord

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedModifiedTupleNode(self)

    def isTypedModifiedTupleNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'TypedModifiedTuple', 'type': self.type.toJson(), 'baseTuple': self.baseTuple.toJson(), 'elements': list(map(optionalASTNodeToJson, self.elements)), 'elementIndices' : self.elementIndices}
    
class ASTTypedTupleAtNode(ASTTypedNode):
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, tuple: ASTNode, index: int, loadResult: bool) -> None:
        super().__init__(sourcePosition, type)
        self.tuple = tuple
        self.index = index
        self.loadResult = loadResult

    def accept(self, visitor: ASTVisitor):
        return visitor.visitTypedTupleAtNode(self)

    def isTypedTupleAtNode(self) -> bool:
        return True

    def toJson(self) -> dict:
        return {'kind': 'TypedTupleAt', 'type': self.type.toJson(), 'tuple': self.tuple.toJson(), 'index': self.index, 'loadResult' : self.loadResult}

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
    def __init__(self, sourcePosition: SourcePosition, type: ASTNode, externalName: Symbol, name: Symbol, value: ASTNode, module: Module) -> None:
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
    
def optionalASTNodeToJson(node: ASTNode) -> dict:
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
    
    def visitBindableNameNode(self, node: ASTBindableNameNode):
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
        self.visitOptionalNode(node.argumentPattern)
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

    def visitFormDecoratedTypeNode(self, node: ASTFormDecoratedTypeNode):
        self.visitNode(node.baseType)

    def visitFormArrayTypeNode(self, node: ASTFormArrayTypeNode):
        self.visitNode(node.elementType)
        self.visitNode(node.size)

    def visitFormPointerTypeNode(self, node: ASTFormPointerTypeNode):
        self.visitNode(node.baseType)

    def visitFormReferenceTypeNode(self, node: ASTFormReferenceTypeNode):
        self.visitNode(node.baseType)

    def visitFormTemporaryReferenceTypeNode(self, node: ASTFormTemporaryReferenceTypeNode):
        self.visitNode(node.baseType)

    def visitFormDictionaryTypeNode(self, node: ASTFormDictionaryTypeNode):
        self.visitNode(node.keyType)
        self.visitNode(node.valueType)

    def visitFormProductTypeNode(self, node: ASTFormProductTypeNode):
        for element in node.elements:
            self.visitNode(element)

    def visitFormRecordTypeNode(self, node: ASTFormRecordTypeNode):
        if node.name is not None:
            self.visitNode(node.name)

        for fieldName in node.fieldNames:
            self.visitNode(fieldName)
        for fieldType in node.fieldTypes:
            self.visitNode(fieldType)

    def visitFormSumTypeNode(self, node: ASTFormSumTypeNode):
        for element in node.elements:
            self.visitNode(element)

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

    def visitArraySubscriptAtNode(self, node: ASTArraySubscriptAtNode):
        self.visitNode(node.pointer)
        self.visitNode(node.index)

    def visitPointerLikeLoadNode(self, node: ASTPointerLikeLoadNode):
        self.visitNode(node.pointer)

    def visitPointerLikeStoreNode(self, node: ASTPointerLikeStoreNode):
        self.visitNode(node.pointer)
        self.visitNode(node.value)

    def visitPointerLikeReinterpretToNode(self, node: ASTPointerLikeReinterpretToNode):
        self.visitNode(node.pointer)
        self.visitNode(node.targetType)

    def visitPointerLikeSubscriptAtNode(self, node: ASTPointerLikeSubscriptAtNode):
        self.visitNode(node.pointer)
        self.visitNode(node.index)

    def visitSequenceNode(self, node: ASTSequenceNode):
        for expression in node.elements:
            self.visitNode(expression)

    def visitDictionaryNode(self, node: ASTDictionaryNode):
        for expression in node.elements:
            self.visitNode(expression)

    def visitTupleNode(self, node: ASTTupleNode):
        for expression in node.elements:
            self.visitOptionalNode(expression)

    def visitRecordNode(self, node: ASTRecordNode):
        self.visitNode(node.type)
        for expression in node.fieldNames:
            self.visitOptionalNode(expression)
        for expression in node.fieldValues:
            self.visitOptionalNode(expression)

    def visitModifiedRecordNode(self, node: ASTModifiedRecordNode):
        self.visitNode(node.record)
        for expression in node.fieldNames:
            self.visitOptionalNode(expression)
        for expression in node.fieldValues:
            self.visitOptionalNode(expression)

    def visitOverloadsTypeNode(self, node: ASTOverloadsTypeNode):
        for expression in node.alternativeTypes:
            self.visitNode(expression)

    def visitDecoratedTypeNode(self, node: ASTDecoratedTypeNode):
        self.visitNode(node.baseType)

    def visitArrayTypeNode(self, node: ASTArrayTypeNode):
        self.visitNode(node.elementType)
        self.visitNode(node.size)

    def visitDictionaryTypeNode(self, node: ASTDictionaryTypeNode):
        self.visitNode(node.keyType)
        self.visitNode(node.valueType)

    def visitPointerTypeNode(self, node: ASTPointerTypeNode):
        self.visitNode(node.baseType)

    def visitReferenceTypeNode(self, node: ASTReferenceTypeNode):
        self.visitNode(node.baseType)

    def visitTemporaryReferenceTypeNode(self, node: ASTTemporaryReferenceTypeNode):
        self.visitNode(node.baseType)
            
    def visitProductTypeNode(self, node: ASTProductTypeNode):
        for expression in node.elementTypes:
            self.visitNode(expression)

    def visitRecordTypeNode(self, node: ASTRecordTypeNode):
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
        self.visitNode(node.valueType)
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

    def visitTypedArraySubscriptAtNode(self, node: ASTTypedArraySubscriptAtNode):
        self.visitNode(node.type)
        self.visitNode(node.array)
        self.visitNode(node.index)

    def visitTypedPointerLikeLoadNode(self, node: ASTTypedPointerLikeLoadNode):
        self.visitNode(node.type)
        self.visitNode(node.pointer)

    def visitTypedPointerLikeStoreNode(self, node: ASTTypedPointerLikeStoreNode):
        self.visitNode(node.type)
        self.visitNode(node.pointer)
        self.visitNode(node.value)

    def visitTypedPointerLikeReinterpretToNode(self, node: ASTTypedPointerLikeReinterpretToNode):
        self.visitNode(node.type)
        self.visitNode(node.pointer)

    def visitTypedPointerLikeSubscriptAtNode(self, node: ASTTypedPointerLikeSubscriptAtNode):
        self.visitNode(node.type)
        self.visitNode(node.pointer)
        self.visitNode(node.index)

    def visitTypedSequenceNode(self, node: ASTTypedSequenceNode):
        self.visitNode(node.type)
        for expression in node.elements:
            self.visitNode(expression)

    def visitTypedDictionaryNode(self, node: ASTTypedDictionaryNode):
        self.visitNode(node.type)
        for expression in node.elements:
            self.visitNode(expression)

    def visitTypedTupleNode(self, node: ASTTypedTupleNode):
        self.visitNode(node.type)
        for expression in node.elements:
            self.visitNode(expression)

    def visitTypedModifiedTupleNode(self, node: ASTTypedModifiedTupleNode):
        self.visitNode(node.type)
        self.visitNode(node.baseTuple)
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

    def visitBindableNameNode(self, node):
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

    def visitFormDecoratedTypeNode(self, node):
        assert False

    def visitFormPointerTypeNode(self, node):
        assert False

    def visitFormReferenceTypeNode(self, node):
        assert False

    def visitFormTemporaryReferenceTypeNode(self, node):
        assert False

    def visitFormArrayTypeNode(self, node):
        assert False

    def visitFormDictionaryTypeNode(self, node):
        assert False

    def visitFormProductTypeNode(self, node):
        assert False

    def visitFormRecordTypeNode(self, node):
        assert False

    def visitFormSumTypeNode(self, node):
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

    def visitArraySubscriptAtNode(self, node: ASTArraySubscriptAtNode):
        assert False

    def visitPointerLikeLoadNode(self, node: ASTPointerLikeLoadNode):
        assert False

    def visitPointerLikeStoreNode(self, node: ASTPointerLikeStoreNode):
        assert False

    def visitPointerLikeReinterpretToNode(self, node: ASTPointerLikeReinterpretToNode):
        assert False

    def visitPointerLikeSubscriptAtNode(self, node: ASTPointerLikeSubscriptAtNode):
        assert False

    def visitDictionaryNode(self, node):
        assert False

    def visitTupleNode(self, node):
        assert False

    def visitRecordNode(self, node):
        assert False

    def visitModifiedRecordNode(self, node):
        assert False
