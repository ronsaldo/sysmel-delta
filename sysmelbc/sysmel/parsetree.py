from abc import ABC, abstractmethod

import os.path
import sys

class SourceCode:
    def __init__(self, directory: str | None, name: str, language: str, text: bytes) -> None:
        self.directory = directory
        self.name = name
        self.language = language
        self.text = text

    def __str__(self) -> str:
        if self.directory is None:
            return self.name
        return os.path.join(self.directory, self.name)

class SourcePosition:
    def __init__(self, sourceCode: SourceCode, startIndex: int, endIndex: int, startLine: int, startColumn: int, endLine: int, endColumn: int) -> None:
        self.sourceCode = sourceCode
        self.startIndex = startIndex
        self.endIndex = endIndex
        self.startLine = startLine
        self.startColumn = startColumn
        self.endLine = endLine
        self.endColumn = endColumn

    def getValue(self) -> bytes:
        return self.sourceCode.text[self.startIndex : self.endIndex]
    
    def getStringValue(self) -> str:
        return self.getValue().decode('utf-8')
    
    def until(self, endSourcePosition):
        return SourcePosition(self.sourceCode,
                self.startIndex, endSourcePosition.startIndex,
                self.startLine, self.startColumn,
                endSourcePosition.startLine, endSourcePosition.startColumn)

    def to(self, endSourcePosition):
        return SourcePosition(self.sourceCode,
                self.startIndex, endSourcePosition.endIndex,
                self.startLine, self.startColumn,
                endSourcePosition.endLine, endSourcePosition.endColumn)

    def __str__(self) -> str:
        return '%s:%d.%d-%d.%d' % (self.sourceCode, self.startLine, self.startColumn, self.endLine, self.endColumn)

class EmptySourcePosition:
    Singleton = None

    @classmethod
    def getSingleton(cls):
        if cls.Singleton is None:
            cls.Singleton = cls()
        return cls.Singleton

    def __str__(self) -> str:
        return '<no position>'
    

class ParseTreeVisitor(ABC):
    def visitNode(self, node):
        return node.accept(self)

    def visitOptionalNode(self, node):
        if node is not None:
            return self.visitNode(node)
        return None

    def visitNodes(self, nodes):
        for node in nodes:
            self.visitNode(node)

    def transformNodes(self, nodes):
        transformed = []
        for node in nodes:
            transformed.append(self.visitNode(node))
        return transformed

    @abstractmethod
    def visitErrorNode(self, node):
        pass

    @abstractmethod
    def visitApplicationNode(self, node):
        pass

    @abstractmethod
    def visitAssignmentNode(self, node):
        pass

    @abstractmethod
    def visitBindPatternNode(self, node):
        pass

    @abstractmethod
    def visitBinaryExpressionSequenceNode(self, node):
        pass

    @abstractmethod
    def visitBindableNameNode(self, node):
        pass

    @abstractmethod
    def visitBlockNode(self, node):
        pass

    @abstractmethod
    def visitCascadeMessageNode(self, node):
        pass

    @abstractmethod
    def visitDictionaryNode(self, node):
        pass

    @abstractmethod
    def visitFunctionalDependentTypeNode(self, node):
        pass

    @abstractmethod
    def visitIdentifierReferenceNode(self, node):
        pass

    @abstractmethod
    def visitLexicalBlockNode(self, node):
        pass

    @abstractmethod
    def visitLiteralCharacterNode(self, node):
        pass

    @abstractmethod
    def visitLiteralFloatNode(self, node):
        pass

    @abstractmethod
    def visitLiteralIntegerNode(self, node):
        pass

    @abstractmethod
    def visitLiteralSymbolNode(self, node):
        pass

    @abstractmethod
    def visitLiteralStringNode(self, node):
        pass

    @abstractmethod
    def visitMessageCascadeNode(self, node):
        pass

    @abstractmethod
    def visitMessageSendNode(self, node):
        pass

    @abstractmethod
    def visitQuasiQuoteNode(self, node):
        pass

    @abstractmethod
    def visitQuasiUnquoteNode(self, node):
        pass

    @abstractmethod
    def visitQuoteNode(self, node):
        pass

    @abstractmethod
    def visitSequenceNode(self, node):
        pass

    @abstractmethod
    def visitSpliceNode(self, node):
        pass

    @abstractmethod
    def visitTupleNode(self, node):
        pass

class ParseTreeNode(ABC):
    def __init__(self, sourcePosition: SourcePosition) -> None:
        self.sourcePosition = sourcePosition

    @abstractmethod
    def accept(self, visitor: ParseTreeVisitor):
        pass

    def asMessageSendCascadeReceiverAndFirstMessage(self):
        return self, None
    
    def isApplicationNode(self) -> bool:
        return False

    def isAssignmentNode(self) -> bool:
        return False

    def isBindPatternNode(self) -> bool:
        return False
    
    def isBinaryExpressionSequenceNode(self) -> bool:
        return False

    def isBindableNameNode(self) -> bool:
        return False
    
    def isBlockNode(self) -> bool:
        return False

    def isDictionaryNode(self) -> bool:
        return False

    def isErrorNode(self) -> bool:
        return False

    def isFunctionalDependentTypeNode(self) -> bool:
        return False

    def isIdentifierReferenceNode(self) -> bool:
        return False

    def isLexicalBlockNode(self) -> bool:
        return False

    def isLiteralNode(self) -> bool:
        return False

    def isLiteralCharacterNode(self) -> bool:
        return False

    def isLiteralFloatNode(self) -> bool:
        return False

    def isLiteralIntegerNode(self) -> bool:
        return False

    def isLiteralStringNode(self) -> bool:
        return False

    def isLiteralSymbolNode(self) -> bool:
        return False

    def isMessageSendNode(self) -> bool:
        return False

    def isQuasiQuoteNode(self) -> bool:
        return False

    def isQuasiUnquoteNode(self) -> bool:
        return False

    def isQuoteNode(self) -> bool:
        return False
    
    def isSpliceNode(self) -> bool:
        return False
    
    def isSequenceNode(self) -> bool:
        return False

    def isTupleNode(self) -> bool:
        return False
    
class ParseTreeErrorNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, message: str, innerNodes: list[ParseTreeNode] = ()) -> None:
        super().__init__(sourcePosition)
        self.message = message
        self.innerNodes = innerNodes
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitErrorNode(self)
    
    def isErrorNode(self) -> bool:
        return True

class ParseTreeApplicationNode(ParseTreeNode):
    Normal = 0
    Bracket = 1
    CurlyBracket = 2
    ByteArrayStart = 3
    Block = 4
    Dictionary = 5

    def __init__(self, sourcePosition: SourcePosition, functional: ParseTreeNode, arguments: list[ParseTreeNode], kind) -> None:
        super().__init__(sourcePosition)
        self.functional = functional
        self.arguments = arguments
        self.kind = kind

    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitApplicationNode(self)
    
    def isApplicationNode(self) -> bool:
        return True

class ParseTreeAssignmentNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, store: ParseTreeNode, value: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.store = store
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitAssignmentNode(self)

    def isAssignmentNode(self) -> bool:
        return True

class ParseTreeBindPatternNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, pattern: ParseTreeNode, value: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.pattern = pattern
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitBindPatternNode(self)

    def isBindPatternNode(self) -> bool:
        return True

class ParseTreeBinaryExpressionSequenceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitBinaryExpressionSequenceNode(self)
    
    def isBinaryExpressionSequenceNode(self) -> bool:
        return True
    
    def asMessageSendCascadeReceiverAndFirstMessage(self):
        assert len(self.elements) >= 3
        if len(self.elements) == 3:
            return self.elements[0], ParseTreeCascadeMessageNode(self.sourcePosition, self.elements[1], [self.elements[2]])
        
        receiverSequence = ParseTreeBinaryExpressionSequenceNode(self.sourcePosition, self.elements[:-2])
        return receiverSequence, ParseTreeCascadeMessageNode(self.sourcePosition, self.elements[-2], [self.elements[-1]])

class ParseTreeBindableNameNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, typeExpression: ParseTreeNode, nameExpression: ParseTreeNode, isImplicit: ParseTreeNode, isExistential: ParseTreeNode, isVariadic: ParseTreeNode, isMutable: ParseTreeNode, hasPostTypeExpression: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.typeExpression = typeExpression
        self.nameExpression = nameExpression
        self.isImplicit = isImplicit
        self.isExistential = isExistential
        self.isVariadic = isVariadic
        self.isMutable = isMutable
        self.hasPostTypeExpression = hasPostTypeExpression
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitBindableNameNode(self)

    def isBindableNameNode(self) -> bool:
        return True
    
class ParseTreeBlockNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, functionType: ParseTreeNode, body: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.functionType = functionType
        self.body = body
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitBlockNode(self)

    def isBlockNode(self) -> bool:
        return True
    
class ParseTreeCascadeMessageNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, selector: ParseTreeNode, arguments: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.selector = selector
        self.arguments = arguments
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitCascadeMessageNode(self)    

    def isCascadeMessageNode(self) -> bool:
        return True

class ParseTreeDictionaryNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitDictionaryNode(self)
    
    def isDictionaryNode(self) -> bool:
        return True
    
class ParseTreeFunctionalDependentTypeNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, argumentPattern: ParseTreeNode, resultType: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.argumentPattern = argumentPattern
        self.resultType = resultType
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitFunctionalDependentTypeNode(self)
    
    def isFunctionalDependentTypeNode(self) -> bool:
        return True
    
class ParseTreeIdentifierReferenceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, value: str) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitIdentifierReferenceNode(self)

    def isIdentifierReferenceNode(self) -> bool:
        return True
    
class ParseTreeLexicalBlockNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, body: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.body = body
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLexicalBlockNode(self)

    def isLexicalBlockNode(self) -> bool:
        return True
    
class ParseTreeLiteralNode(ParseTreeNode):
    def isLiteralNode(self) -> bool:
        return True

class ParseTreeLiteralCharacterNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: int) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralCharacterNode(self)

    def isLiteralCharacterNode(self) -> bool:
        return True

class ParseTreeLiteralFloatNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: float) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralFloatNode(self)

    def isLiteralFloatNode(self) -> bool:
        return True
        
class ParseTreeLiteralIntegerNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: int) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralIntegerNode(self)

    def isLiteralIntegerNode(self) -> bool:
        return True
    
class ParseTreeLiteralStringNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: str) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralStringNode(self)    

    def isLiteralStringNode(self) -> bool:
        return True
    
class ParseTreeLiteralSymbolNode(ParseTreeLiteralNode):
    def __init__(self, sourcePosition: SourcePosition, value: str) -> None:
        super().__init__(sourcePosition)
        self.value = value
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitLiteralSymbolNode(self)

    def isLiteralSymbolNode(self) -> bool:
        return True
    
class ParseTreeMessageCascadeNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, receiver: ParseTreeNode, messages: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.receiver = receiver
        self.messages = messages
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitMessageCascadeNode(self)    

    def isMessageCascadeNode(self) -> bool:
        return True
    
class ParseTreeMessageSendNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, receiver: ParseTreeNode, selector: ParseTreeNode, arguments: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.receiver = receiver
        self.selector = selector
        self.arguments = arguments
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitMessageSendNode(self)    

    def isMessageSendNode(self) -> bool:
        return True
    
    def asMessageSendCascadeReceiverAndFirstMessage(self):
        return self.receiver, ParseTreeCascadeMessageNode(self.sourcePosition, self.selector, self.arguments)

class ParseTreeQuasiQuoteNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, term: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.term = term
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitQuasiQuoteNode(self)

    def isQuasiQuoteNode(self) -> bool:
        return True
    
class ParseTreeQuasiUnquoteNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, term: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.term = term
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitQuasiUnquoteNode(self)

    def isQuasiUnquoteNode(self) -> bool:
        return True

class ParseTreeQuoteNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, term: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.term = term
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitQuoteNode(self)

    def isQuoteNode(self) -> bool:
        return True
    
class ParseTreeSequenceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitSequenceNode(self)

    def isSequenceNode(self) -> bool:
        return True
    
class ParseTreeSpliceNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, term: ParseTreeNode) -> None:
        super().__init__(sourcePosition)
        self.term = term
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitSpliceNode(self)

    def isSpliceNode(self) -> bool:
        return True

class ParseTreeTupleNode(ParseTreeNode):
    def __init__(self, sourcePosition: SourcePosition, elements: list[ParseTreeNode]) -> None:
        super().__init__(sourcePosition)
        self.elements = elements
    
    def accept(self, visitor: ParseTreeVisitor):
        return visitor.visitTupleNode(self)
    
    def isTupleNode(self) -> bool:
        return True
    
class ParseTreeSequentialVisitor(ParseTreeVisitor):
    def visitErrorNode(self, node: ParseTreeErrorNode):
        self.visitNodes(node.innerNodes)

    def visitApplicationNode(self, node: ParseTreeApplicationNode):
        self.visitNode(node.functional)
        self.visitNodes(node.arguments)

    def visitAssignmentNode(self, node: ParseTreeAssignmentNode):
        self.visitNode(node.store)
        self.visitNode(node.value)

    def visitBindPatternNode(self, node: ParseTreeBindPatternNode):
        self.visitNode(node.pattern)
        self.visitNode(node.value)

    def visitBinaryExpressionSequenceNode(self, node: ParseTreeBinaryExpressionSequenceNode):
        self.visitNodes(node.elements)

    def visitBindableNameNode(self, node: ParseTreeBindableNameNode):
        self.visitOptionalNode(node.typeExpression)
        self.visitOptionalNode(node.nameExpression)

    def visitBlockNode(self, node: ParseTreeBlockNode):
        self.visitNode(node.functionType)
        self.visitNode(node.body)

    def visitCascadeMessageNode(self, node: ParseTreeCascadeMessageNode):
        self.visitNode(node.selector)
        self.visitNodes(node.arguments)

    def visitDictionaryNode(self, node: ParseTreeDictionaryNode):
        self.visitNodes(node.elements)

    def visitFunctionalDependentTypeNode(self, node: ParseTreeFunctionalDependentTypeNode):
        self.visitOptionalNode(node.argumentPattern)
        self.visitOptionalNode(node.resultType)

    def visitIdentifierReferenceNode(self, node: ParseTreeIdentifierReferenceNode):
        pass

    def visitLexicalBlockNode(self, node: ParseTreeLexicalBlockNode):
        self.visitNode(node.body)

    def visitLiteralNode(self, node: ParseTreeLiteralNode):
        pass

    def visitLiteralCharacterNode(self, node: ParseTreeLiteralCharacterNode):
        self.visitLiteralNode(node)

    def visitLiteralFloatNode(self, node: ParseTreeLiteralFloatNode):
        self.visitLiteralNode(node)

    def visitLiteralIntegerNode(self, node: ParseTreeLiteralIntegerNode):
        self.visitLiteralNode(node)

    def visitLiteralSymbolNode(self, node: ParseTreeLiteralSymbolNode):
        self.visitLiteralNode(node)

    def visitLiteralStringNode(self, node: ParseTreeLiteralStringNode):
        self.visitLiteralNode(node)

    def visitMessageCascadeNode(self, node: ParseTreeMessageCascadeNode):
        self.visitNode(node.receiver)
        self.visitNodes(node.messages)

    def visitMessageSendNode(self, node: ParseTreeMessageSendNode):
        self.visitOptionalNode(node.receiver)
        self.visitNode(node.selector)
        self.visitNodes(node.arguments)

    def visitQuoteNode(self, node: ParseTreeQuoteNode):
        self.visitNode(node.term)

    def visitQuasiQuoteNode(self, node: ParseTreeQuasiQuoteNode):
        self.visitNode(node.term)

    def visitQuasiUnquoteNode(self, node: ParseTreeQuasiUnquoteNode):
        self.visitNode(node.term)

    def visitSequenceNode(self, node: ParseTreeSequenceNode):
        self.visitNodes(node.elements)

    def visitSpliceNode(self, node: ParseTreeSpliceNode):
        self.visitNode(node.term)

    def visitTupleNode(self, node: ParseTreeTupleNode):
        self.visitNodes(node.elements)

class ParseTreeErrorVisitor(ParseTreeSequentialVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.errorNodes: list[ParseTreeErrorNode] = []
    
    def visitErrorNode(self, node: ParseTreeErrorNode):
        self.errorNodes.append(node)
        super().visitErrorNode(node)

    def checkAndPrintErrors(self, node: ParseTreeNode):
        self.visitNode(node)
        for errorNode in self.errorNodes:
            sys.stderr.write('%s: %s\n' % (str(errorNode.sourcePosition), errorNode.message))
        return len(self.errorNodes) == 0
    