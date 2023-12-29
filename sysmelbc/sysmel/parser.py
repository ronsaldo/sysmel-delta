from .scanner import SourceCode, SourcePosition, Token, TokenKind, scanFileNamed
from .ast import *
from .value import *
import copy

C_ESCAPE_TABLE = {
    'r': '\r',
    'n': '\n',
    't': '\t',
}

class ParserState:
    def __init__(self, sourceCode: SourceCode, tokens: list[Token]) -> None:
        self.sourceCode = sourceCode
        self.tokens = tokens
        self.position = 0

    def atEnd(self) -> bool:
        return self.position >= len(self.tokens) or self.peekKind() == TokenKind.END_OF_SOURCE

    def peekKind(self, offset: int = 0) -> TokenKind:
        peekPosition = self.position + offset
        if peekPosition < len(self.tokens):
            return self.tokens[peekPosition].kind
        else:
            return TokenKind.END_OF_SOURCE

    def peek(self, offset: int = 0) -> Token:
        peekPosition = self.position + offset
        if peekPosition < len(self.tokens):
            return self.tokens[peekPosition]
        else:
            return None
        
    def advance(self) -> None:
        assert self.position < len(self.tokens)
        self.position += 1

    def next(self) -> Token:
        token = self.tokens[self.position]
        self.position += 1
        return token

    def expectAddingErrorToNode(self, expectedKind: TokenKind, node: ASTNode) -> ASTNode:
        if self.peekKind() == expectedKind:
            self.advance()
            return node
        
        errorPosition = self.currentSourcePosition()
        errorNode = ASTErrorNode(errorPosition, "Expected token of kind %s." % str(expectedKind))
        return ASTSequenceNode(node.sourcePosition.to(errorPosition), [node, errorNode])

    def currentSourcePosition(self) -> SourcePosition:
        if self.position < len(self.tokens):
            return self.tokens[self.position].sourcePosition

        assert self.tokens[-1].kind == TokenKind.END_OF_SOURCE 
        return self.tokens[-1].sourcePosition

    def previousSourcePosition(self) -> SourcePosition:
        assert self.position > 0
        return self.tokens[self.position - 1].sourcePosition

    def sourcePositionFrom(self, startingPosition: int) -> SourcePosition:
        assert startingPosition < len(self.tokens)
        startSourcePosition = self.tokens[startingPosition].sourcePosition
        if self.position > 0:
            endSourcePosition = self.previousSourcePosition()
            return startSourcePosition.to(endSourcePosition)
        else:
            endSourcePosition = self.currentSourcePosition()
            return startSourcePosition.until(endSourcePosition)
    
    def advanceWithExpectedError(self, message: str):
        if self.peekKind() == TokenKind.ERROR:
            errorToken = self.next()
            return self, ASTErrorNode(errorToken.sourcePosition, errorToken.errorMessage)
        elif self.atEnd():
            return self, ASTErrorNode(self.currentSourcePosition(), message)
        else:
            errorPosition = self.currentSourcePosition()
            self.advance()
            return self, ASTErrorNode(errorPosition, message)

def parseCEscapedString(string: str) -> str:
    unescaped = ''
    i = 0
    while i < len(string):
        c = string[i]
        if c == '\\':
            i += 1
            c = string[i]
            c = C_ESCAPE_TABLE.get(c, c)
        unescaped += c
    return unescaped

def parseLiteralInteger(state: ParserState) -> tuple[ParserState, ASTNode]:
    token = state.next()
    assert token.kind == TokenKind.INTEGER
    return state, ASTLiteralNode(token.sourcePosition, IntegerValue(int(token.getValue())))

def parseLiteralFloat(state: ParserState) -> tuple[ParserState, ASTNode]:
    token = state.next()
    assert token.kind == TokenKind.FLOAT
    return state, ASTLiteralNode(token.sourcePosition, FloatValue(float(token.getValue())))

def parseLiteralString(state: ParserState) -> tuple[ParserState, ASTNode]:
    token = state.next()
    assert token.kind == TokenKind.STRING
    return state, ASTLiteralNode(token.sourcePosition, StringValue(parseCEscapedString(token.getStringValue()[1:-1])))

def parseLiteralCharacter(state: ParserState) -> tuple[ParserState, ASTNode]:
    token = state.next()
    assert token.kind == TokenKind.CHARACTER
    return state, ASTLiteralNode(token.sourcePosition, CharacterValue(ord(parseCEscapedString(token.getStringValue()[1:-1])[0])))

def parseLiteralSymbol(state: ParserState) -> tuple[ParserState, ASTNode]:
    token = state.next()
    assert token.kind == TokenKind.SYMBOL
    symbolValue = token.getValue()[1:]
    if symbolValue[0] == '"':
        assert symbolValue[0] == '"' and symbolValue[-1] == '"'
        symbolValue = parseCEscapedString(symbolValue[1:-1])
    return state, ASTLiteralNode(token.sourcePosition, Symbol.intern(symbolValue))

def parseLiteral(state: ParserState) -> tuple[ParserState, ASTNode]:
    if state.peekKind() == TokenKind.INTEGER: return parseLiteralInteger(state)
    elif state.peekKind() == TokenKind.FLOAT: return parseLiteralFloat(state)
    elif state.peekKind() == TokenKind.STRING: return parseLiteralString(state)
    elif state.peekKind() == TokenKind.CHARACTER: return parseLiteralCharacter(state)
    elif state.peekKind() == TokenKind.SYMBOL: return parseLiteralSymbol(state)
    else: return state.advanceWithExpectedError("Literal")

def parseIdentifier(state: ParserState) -> tuple[ParserState, ASTNode]:
    token = state.next()
    assert token.kind == TokenKind.IDENTIFIER
    return state, ASTIdentifierReferenceNode(token.sourcePosition, Symbol.intern(token.getStringValue()))

def parseTerm(state: ParserState) -> tuple[ParserState, ASTNode]:
    if state.peekKind() == TokenKind.IDENTIFIER: return parseIdentifier(state)
    elif state.peekKind() == TokenKind.LEFT_PARENT: return parseParenthesisOrLambda(state)
    elif state.peekKind() == TokenKind.LEFT_CURLY_BRACKET: return parseBlock(state)
    else: return parseLiteral(state)

def parseOptionalParenthesis(state: ParserState) -> tuple[ParserState, ASTNode]:
    if state.peekKind() == TokenKind.LEFT_PARENT:
        return parseParenthesis(state)
    else:
        return state, None

def parseNameExpression(state: ParserState) -> tuple[ParserState, ASTNode]:
    if state.peekKind() == TokenKind.IDENTIFIER:
        token = state.next()
        return state, ASTLiteralNode(token.sourcePosition, Symbol.intern(token.getStringValue()))
    else:
        assert False

def parseOptionalNameExpression(state: ParserState) -> tuple[ParserState, ASTNode]:
    if state.peekKind() in [TokenKind.IDENTIFIER]:
        return parseNameExpression(state)
    else:
        return state, None

def parseArgument(state: ParserState) -> tuple[ParserState, ASTNode]:
    startPosition = state.position
    assert state.peekKind() == TokenKind.COLON
    state.advance()

    isForAll = False
    if state.peekKind() == TokenKind.STAR:
        state.advance()
        isForAll = True

    state, typeExpression = parseOptionalParenthesis(state)
    state, nameExpression = parseOptionalNameExpression(state)

    return state, ASTArgumentNode(state.sourcePositionFrom(startPosition), typeExpression, nameExpression, isForAll)    

def parseFunctionalType(state: ParserState) -> tuple[ParserState, ASTNode]:
    startPosition = state.position
    arguments = []
    while state.peekKind() == TokenKind.COLON:
        state, argument = parseArgument(state)
        arguments.append(argument)
    
    resultTypeExpression = None
    hasResultTypeExpression = state.peekKind() == TokenKind.COLON_COLON
    if hasResultTypeExpression:
        state.advance()
        state, resultTypeExpression = parseUnaryPostfixExpression(state)
    
    if len(arguments) == 0 and not hasResultTypeExpression:
        return state, None
    return state, ASTFunctionalTypeNode(state.sourcePositionFrom(startPosition), arguments, resultTypeExpression)

def parseParenthesis(state: ParserState) -> tuple[ParserState, ASTNode]:
    # (
    startPosition = state.position
    assert state.peekKind() == TokenKind.LEFT_PARENT
    state.advance()

    if state.peekKind() == TokenKind.RIGHT_PARENT:
        state.advance()
        return state, ASTTupleNode(state.sourcePositionFrom(startPosition), [])
    
    if state.peekKind() in [TokenKind.COLON, TokenKind.COLON_COLON]:
        state, expression = parseFunctionalType(state)
    else:
        state, expression = parseExpression(state)

    # )
    expression = state.expectAddingErrorToNode(TokenKind.RIGHT_PARENT, expression)
    return state, expression

def parseParenthesisOrLambda(state: ParserState) -> tuple[ParserState, ASTNode]:
    startPosition = state.position

    if state.peekKind() == TokenKind.LEFT_PARENT and \
        state.peekKind(1) == TokenKind.RIGHT_PARENT and \
        state.peekKind(2) == TokenKind.ASSIGNMENT_ARROW:
        state.advance()
        state.advance()
        expression = ASTFunctionalTypeNode(state.sourcePositionFrom(startPosition), [], None)
    else:
        state, expression = parseParenthesis(state)

    if state.peekKind() == TokenKind.ASSIGNMENT_ARROW:
        state.advance()
        functionalType = expression
        state, body = parseExpression(state)
        return state, ASTLambdaNode(state.sourcePositionFrom(startPosition), functionalType, body)
    else:
        return state, expression

def parseBlock(state: ParserState) -> tuple[ParserState, ASTNode]:
    # {
    startPosition = state.position
    assert state.peekKind() == TokenKind.LEFT_CURLY_BRACKET
    state.advance()

    functionalType = None
    if state.peekKind() in [TokenKind.COLON, TokenKind.COLON_COLON]:
        state, functionalType = parseFunctionalType(state)
        functionalType = state.expectAddingErrorToNode(TokenKind.BAR, functionalType)
    elif state.peekKind() == TokenKind.BAR:
        functionalType = ASTFunctionalTypeNode(state.currentSourcePosition(), [], None)

    state, body = parseSequenceUntilEndOrDelimiter(state, TokenKind.RIGHT_CURLY_BRACKET)

    # }
    body = state.expectAddingErrorToNode(TokenKind.RIGHT_CURLY_BRACKET, body)
    if functionalType is None:
        return state, ASTLexicalBlockNode(state.sourcePositionFrom(startPosition), body)
    else:
        return state, ASTBlockNode(state.sourcePositionFrom(startPosition), functionalType, body)

def parseUnaryPostfixExpression(state: ParserState) -> tuple[ParserState, ASTNode]:
    startPosition = state.position
    state, receiver = parseTerm(state)
    while state.peekKind() in [TokenKind.IDENTIFIER, TokenKind.LEFT_PARENT]:
        token = state.next()
        if token.kind == TokenKind.IDENTIFIER:
            selector = ASTLiteralNode(token.sourcePosition, Symbol.intern(token.getStringValue()))
            receiver = ASTMessageSendNode(receiver.sourcePosition.to(selector.sourcePosition), receiver, selector, [])
        elif token.kind == TokenKind.LEFT_PARENT:
            state, arguments = parseExpressionListUntilEndOrDelimiter(state, TokenKind.RIGHT_PARENT)
            if state.peekKind() == TokenKind.RIGHT_PARENT:
                state.advance()
            else:
                arguments.append(ASTErrorNode(state.currentSourcePosition, "Expected right parenthesis."))
            receiver = ASTApplicationNode(state.sourcePositionFrom(startPosition), receiver, arguments)
    return state, receiver

def isBinaryExpressionOperator(kind: TokenKind) -> bool:
    return kind in [TokenKind.OPERATOR, TokenKind.STAR, TokenKind.LESS_THAN, TokenKind.GREATER_THAN, TokenKind.BAR]

def parseBinaryExpressionSequence(state: ParserState) -> tuple[ParserState, ASTNode]:
    startPosition = state.position
    state, operand = parseUnaryPostfixExpression(state)
    if not isBinaryExpressionOperator(state.peekKind()):
        return state, operand
    
    elements = [operand]
    while isBinaryExpressionOperator(state.peekKind()):
        operatorToken = state.next()
        operator = ASTLiteralNode(operatorToken.sourcePosition, Symbol.intern(operatorToken.getStringValue()))
        elements.append(operator)

        state, operand = parseUnaryPostfixExpression(state)
        elements.append(operand)

    return state, ASTBinaryExpressionSequenceNode(state.sourcePositionFrom(startPosition), elements)

def parseKeywordApplication(state: ParserState) -> tuple[ParserState, ASTNode]:
    assert state.peekKind() == TokenKind.KEYWORD
    startPosition = state.position

    symbolValue = ""
    arguments = []
    firstKeywordSourcePosition = state.peek(0).sourcePosition
    lastKeywordSourcePosition = firstKeywordSourcePosition
    while state.peekKind() == TokenKind.KEYWORD:
        keywordToken = state.next()
        lastKeywordSourcePosition = keywordToken.sourcePosition
        symbolValue += keywordToken.getStringValue()
        
        state, argument = parseBinaryExpressionSequence(state)
        arguments.append(argument)

    functionIdentifier = ASTIdentifierReferenceNode(firstKeywordSourcePosition.to(lastKeywordSourcePosition), Symbol.intern(symbolValue))
    return state, ASTApplicationNode(state.sourcePositionFrom(startPosition), functionIdentifier, arguments)

def parseCommaExpressionElement(state: ParserState) -> tuple[ParserState, ASTNode]:
    if state.peekKind() == TokenKind.KEYWORD:
        return parseKeywordApplication(state)
    return parseBinaryExpressionSequence(state)

def parseCommaExpression(state: ParserState) -> tuple[ParserState, ASTNode]:
    startPosition = state.position
    state, element = parseCommaExpressionElement(state)
    if state.peekKind() != TokenKind.COMMA:
        return state, element
    
    elements = [element]
    while state.peekKind() == TokenKind.COMMA:
        state.advance()
        state, element = parseCommaExpressionElement(state)
        elements.append(element)
    
    return state, ASTTupleNode(state.sourcePositionFrom(startPosition), elements)

def parseExpression(state: ParserState) -> tuple[ParserState, ASTNode]:
    return parseCommaExpression(state)

def parseExpressionListUntilEndOrDelimiter(state: ParserState, delimiter: TokenKind) -> tuple[ParserState, list[ASTNode]]:
    elements = []

    # Chop the initial dots
    while state.peekKind() == TokenKind.DOT:
        state.advance()

    # Parse the next expression
    expectsExpression = True
    while not state.atEnd() and state.peekKind() != delimiter:
        if not expectsExpression:
            elements.append(ASTErrorNode(state.currentSourcePosition(), "Expected dot before expression."))

        state, expression = parseExpression(state)
        elements.append(expression)

        expectsExpression = False
        # Chop the next dot sequence
        while state.peekKind() == TokenKind.DOT:
            expectsExpression = True
            state.advance()

    return state, elements

def parseSequenceUntilEndOrDelimiter(state: ParserState, delimiter: TokenKind) -> tuple[ParserState, ASTNode]:
    initialPosition = state.position
    state, elements = parseExpressionListUntilEndOrDelimiter(state, delimiter)
    return state, ASTSequenceNode(state.sourcePositionFrom(initialPosition), elements)

def parseTopLevelExpression(state: ParserState) -> tuple[ParserState, ASTNode]:
    state, node = parseSequenceUntilEndOrDelimiter(state, TokenKind.END_OF_SOURCE)
    return node

def parseFileNamed(fileName: str) -> ASTNode:
    sourceCode, tokens = scanFileNamed(fileName)
    state = ParserState(sourceCode, tokens)
    return parseTopLevelExpression(state)
    