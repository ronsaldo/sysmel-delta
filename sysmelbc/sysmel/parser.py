from .scanner import Token, TokenKind, scanFileNamed
from .parsetree import *
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

    def expectAddingErrorToNode(self, expectedKind: TokenKind, node: ParseTreeNode) -> ParseTreeNode:
        if self.peekKind() == expectedKind:
            self.advance()
            return node
        
        errorPosition = self.currentSourcePosition()
        errorNode = ParseTreeErrorNode(errorPosition, "Expected token of kind %s." % str(expectedKind))
        return ParseTreeSequenceNode(node.sourcePosition.to(errorPosition), [node, errorNode])

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
            return self, ParseTreeErrorNode(errorToken.sourcePosition, errorToken.errorMessage)
        elif self.atEnd():
            return self, ParseTreeErrorNode(self.currentSourcePosition(), message)
        else:
            errorPosition = self.currentSourcePosition()
            self.advance()
            return self, ParseTreeErrorNode(errorPosition, message)

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
        i += 1
    return unescaped

def parseLiteralInteger(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.NAT
    return state, ParseTreeLiteralIntegerNode(token.sourcePosition, int(token.getValue()))

def parseLiteralFloat(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.FLOAT
    return state, ParseTreeLiteralFloatNode(token.sourcePosition, float(token.getValue()))

def parseLiteralString(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.STRING
    return state, ParseTreeLiteralStringNode(token.sourcePosition, parseCEscapedString(token.getStringValue()[1:-1]))

def parseLiteralCharacter(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.CHARACTER
    return state, ParseTreeLiteralCharacterNode(token.sourcePosition, ord(parseCEscapedString(token.getStringValue()[1:-1])[0]))

def parseLiteralSymbol(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.SYMBOL
    symbolValue = token.getStringValue()[1:]
    if symbolValue[0] == '"':
        assert symbolValue[0] == '"' and symbolValue[-1] == '"'
        symbolValue = parseCEscapedString(symbolValue[1:-1])
    return state, ParseTreeLiteralSymbolNode(token.sourcePosition, symbolValue)

def parseLiteral(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.NAT: return parseLiteralInteger(state)
    elif state.peekKind() == TokenKind.FLOAT: return parseLiteralFloat(state)
    elif state.peekKind() == TokenKind.STRING: return parseLiteralString(state)
    elif state.peekKind() == TokenKind.CHARACTER: return parseLiteralCharacter(state)
    elif state.peekKind() == TokenKind.SYMBOL: return parseLiteralSymbol(state)
    else: return state.advanceWithExpectedError('Expected a literal.')

def parseIdentifier(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    token = state.next()
    assert token.kind == TokenKind.IDENTIFIER
    return state, ParseTreeIdentifierReferenceNode(token.sourcePosition, token.getStringValue())

def parseQuote(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.next().kind == TokenKind.QUOTE
    term = parseTerm(state)
    return state, ParseTreeQuoteNode(state.sourcePositionFrom(startPosition), term)

def parseQuasiQuote(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.next().kind == TokenKind.QUOTE
    term = parseTerm(state)
    return state, ParseTreeQuasiQuoteNode(state.sourcePositionFrom(startPosition), term)

def parseQuasiUnquote(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.next().kind == TokenKind.QUOTE
    term = parseTerm(state)
    return state, ParseTreeQuasiUnquoteNode(state.sourcePositionFrom(startPosition), term)

def parseSplice(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.next().kind == TokenKind.QUOTE
    term = parseTerm(state)
    return state, ParseTreeSpliceNode(state.sourcePositionFrom(startPosition), term)

def parseTerm(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.IDENTIFIER: return parseIdentifier(state)
    elif state.peekKind() == TokenKind.LEFT_PARENT: return parseParenthesis(state)
    elif state.peekKind() == TokenKind.LEFT_CURLY_BRACKET: return parseBlock(state)
    elif state.peekKind() == TokenKind.DICTIONARY_START: return parseDictionary(state)
    elif state.peekKind() == TokenKind.COLON: return parseBindableName(state)
    elif state.peekKind() == TokenKind.QUOTE: return parseQuote(state)
    elif state.peekKind() == TokenKind.QUASI_QUOTE: return parseQuasiQuote(state)
    elif state.peekKind() == TokenKind.QUASI_UNQUOTE: return parseQuasiUnquote(state)
    elif state.peekKind() == TokenKind.SPLICE: return parseSplice(state)
    else: return parseLiteral(state)

def parseOptionalParenthesis(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.LEFT_PARENT:
        return parseParenthesis(state)
    else:
        return state, None

def parseNameExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.IDENTIFIER:
        token = state.next()
        return state, ParseTreeLiteralSymbolNode(token.sourcePosition, token.getStringValue())
    else:
        return state, ParseTreeErrorNode(state.currentSourcePosition(), 'Expected a bindable name.')

def parseOptionalBindableNameType(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.LEFT_BRACKET:
        state.advance()
        state, typeExpression  = parseExpression(state)
        typeExpression = state.expectAddingErrorToNode(TokenKind.RIGHT_BRACKET, typeExpression)
        return True, state, typeExpression
    elif state.peekKind() == TokenKind.LEFT_PARENT:
        state.advance()
        state, typeExpression = parseExpression(state)
        typeExpression = state.expectAddingErrorToNode(TokenKind.RIGHT_PARENT, typeExpression)
        return False, state, typeExpression
    return False, state, None

def parseBindableName(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    assert state.peekKind() == TokenKind.COLON
    state.advance()

    isExistential = False
    isMutable = False
    if state.peekKind() == TokenKind.BANG:
        isMutable = True
        state.advance()
    if state.peekKind() == TokenKind.QUESTION:
        isExistential = isExistential or state.peekKind() == TokenKind.QUESTION
        state.advance()

    isImplicit, state, typeExpression = parseOptionalBindableNameType(state)
    hasPostTypeExpression = False

    isVariadic = False
    if state.peekKind() == TokenKind.ELLIPSIS:
        state.advance()
        isVariadic = True
        nameExpression = None
    else:
        state, nameExpression = parseNameExpression(state)
        if typeExpression is None:
            isImplicit, state, typeExpression = parseOptionalBindableNameType(state)
            hasPostTypeExpression = typeExpression is not None

        if state.peekKind() == TokenKind.ELLIPSIS:
            state.advance()
            isVariadic = True

    return state, ParseTreeBindableNameNode(state.sourcePositionFrom(startPosition), typeExpression, nameExpression, isImplicit, isExistential, isVariadic, isMutable, hasPostTypeExpression)

def parseParenthesis(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    # (
    startPosition = state.position
    assert state.peekKind() == TokenKind.LEFT_PARENT
    state.advance()

    if isBinaryExpressionOperator(state.peekKind()) and state.peekKind(1) == TokenKind.RIGHT_PARENT:
        token = state.next()
        state.advance()
        return state, ParseTreeIdentifierReferenceNode(token.sourcePosition, token.getStringValue())

    if state.peekKind() == TokenKind.RIGHT_PARENT:
        state.advance()
        return state, ParseTreeTupleNode(state.sourcePositionFrom(startPosition), [])
    
    state, expression = parseSequenceUntilEndOrDelimiter(state, TokenKind.RIGHT_PARENT)

    # )
    expression = state.expectAddingErrorToNode(TokenKind.RIGHT_PARENT, expression)
    return state, expression

def parseBlock(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    # {
    startPosition = state.position
    assert state.peekKind() == TokenKind.LEFT_CURLY_BRACKET
    state.advance()

    functionalType = None
    if state.peekKind() == TokenKind.BAR:
        state.advance()
        if state.peekKind() == TokenKind.BAR:
            state.advance()
            functionalType = ParseTreeFunctionalDependentTypeNode(state.currentSourcePosition(), None, None)
        else:
            state, functionalType = parseFunctionalType(state)
            state.expectAddingErrorToNode(TokenKind.BAR, functionalType)
            if not functionalType.isFunctionalDependentTypeNode():
                functionalType = ParseTreeFunctionalDependentTypeNode(state.currentSourcePosition(), functionalType, None)

    state, body = parseSequenceUntilEndOrDelimiter(state, TokenKind.RIGHT_CURLY_BRACKET)

    # }
    body = state.expectAddingErrorToNode(TokenKind.RIGHT_CURLY_BRACKET, body)
    if functionalType is None:
        return state, ParseTreeLexicalBlockNode(state.sourcePositionFrom(startPosition), body)
    else:
        return state, ParseTreeBlockNode(state.sourcePositionFrom(startPosition), functionalType, body)

def parseDictionaryAssociation(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    value = None
    if state.peekKind() == TokenKind.KEYWORD:
        keyToken = state.next()
        key = ParseTreeLiteralSymbolNode(keyToken.sourcePosition, keyToken.getStringValue()[:-1])

        if state.peekKind() not in [TokenKind.DOT, TokenKind.RIGHT_CURLY_BRACKET]:
            state, value = parseAssociationExpression(state)
    else:
        state, key = parseBinaryExpressionSequence(state)
        if state.peekKind() == TokenKind.COLON:
            state.advance()
            state, value = parseAssociationExpression(state)

    return state, ParseTreeTupleNode(state.sourcePositionFrom(startPosition), [key, value])

def parseDictionary(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    # #{
    startPosition = state.position
    assert state.peekKind() == TokenKind.DICTIONARY_START
    state.advance()

    # Chop the initial dots
    while state.peekKind() == TokenKind.DOT:
        state.advance()

    # Parse the next expression
    expectsExpression = True
    elements = []
    while not state.atEnd() and state.peekKind() != TokenKind.RIGHT_CURLY_BRACKET:
        if not expectsExpression:
            elements.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected dot before association."))

        state, expression = parseDictionaryAssociation(state)
        elements.append(expression)

        expectsExpression = False
        # Chop the next dot sequence
        while state.peekKind() == TokenKind.DOT:
            expectsExpression = True
            state.advance()

    # }
    if state.peekKind() == TokenKind.RIGHT_CURLY_BRACKET:
        state.advance()
    else:
        elements.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected a right curly brack (})."))

    return state, ParseTreeDictionaryNode(state.sourcePositionFrom(startPosition), elements)

def parseUnaryPostfixExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, receiver = parseTerm(state)
    while state.peekKind() in [TokenKind.IDENTIFIER, TokenKind.LEFT_PARENT, TokenKind.LEFT_BRACKET, TokenKind.LEFT_CURLY_BRACKET, TokenKind.BYTE_ARRAY_START, TokenKind.DICTIONARY_START]:
        token = state.peek()
        if token.kind == TokenKind.IDENTIFIER:
            state.advance()
            selector = ParseTreeLiteralSymbolNode(token.sourcePosition, token.getStringValue())
            receiver = ParseTreeMessageSendNode(receiver.sourcePosition.to(selector.sourcePosition), receiver, selector, [])
        elif token.kind == TokenKind.LEFT_PARENT:
            state.advance()
            state, arguments = parseExpressionListUntilEndOrDelimiter(state, TokenKind.RIGHT_PARENT)
            if state.peekKind() == TokenKind.RIGHT_PARENT:
                state.advance()
            else:
                arguments.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected right parenthesis."))
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, arguments, ParseTreeApplicationNode.Normal)
        elif token.kind == TokenKind.LEFT_BRACKET:
            state.advance()
            state, arguments = parseExpressionListUntilEndOrDelimiter(state, TokenKind.RIGHT_BRACKET)
            if state.peekKind() == TokenKind.RIGHT_BRACKET:
                state.advance()
            else:
                arguments.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected right bracket."))
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, arguments, ParseTreeApplicationNode.Bracket)
        elif token.kind == TokenKind.BYTE_ARRAY_START:
            state.advance()
            state, arguments = parseExpressionListUntilEndOrDelimiter(state, TokenKind.RIGHT_BRACKET)
            if state.peekKind() == TokenKind.RIGHT_BRACKET:
                state.advance()
            else:
                arguments.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected right bracket."))
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, arguments, ParseTreeApplicationNode.ByteArrayStart)
        elif token.kind == TokenKind.LEFT_CURLY_BRACKET:
            state, argument = parseBlock(state)
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, [argument], ParseTreeApplicationNode.Block)
        elif token.kind == TokenKind.DICTIONARY_START:
            state, argument = parseDictionary(state)
            receiver = ParseTreeApplicationNode(state.sourcePositionFrom(startPosition), receiver, [argument], ParseTreeApplicationNode.Dictionary)
    return state, receiver

def isBinaryExpressionOperator(kind: TokenKind) -> bool:
    return kind in [TokenKind.OPERATOR, TokenKind.STAR, TokenKind.LESS_THAN, TokenKind.GREATER_THAN, TokenKind.BAR]

def parseBinaryExpressionSequence(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, operand = parseUnaryPostfixExpression(state)
    if not isBinaryExpressionOperator(state.peekKind()):
        return state, operand
    
    elements = [operand]
    while isBinaryExpressionOperator(state.peekKind()):
        operatorToken = state.next()
        operator = ParseTreeLiteralSymbolNode(operatorToken.sourcePosition, operatorToken.getStringValue())
        elements.append(operator)

        state, operand = parseUnaryPostfixExpression(state)
        elements.append(operand)

    return state, ParseTreeBinaryExpressionSequenceNode(state.sourcePositionFrom(startPosition), elements)

def parseAssociationExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, key = parseBinaryExpressionSequence(state)

    if state.peekKind() != TokenKind.COLON:
        return state, key
    
    state.advance()
    state, value = parseAssociationExpression(state)
    return state, ParseTreeTupleNode(state.sourcePositionFrom(startPosition), [key, value])
    
def parseKeywordApplication(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
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
        
        state, argument = parseAssociationExpression(state)
        arguments.append(argument)

    functionIdentifier = ParseTreeLiteralSymbolNode(firstKeywordSourcePosition.to(lastKeywordSourcePosition), symbolValue)
    return state, ParseTreeMessageSendNode(state.sourcePositionFrom(startPosition), None, functionIdentifier, arguments)

def parseKeywordMessageSend(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, receiver = parseAssociationExpression(state)
    if state.peekKind() != TokenKind.KEYWORD:
        return state, receiver

    symbolValue = ""
    arguments = []
    firstKeywordSourcePosition = state.peek(0).sourcePosition
    lastKeywordSourcePosition = firstKeywordSourcePosition
    while state.peekKind() == TokenKind.KEYWORD:
        keywordToken = state.next()
        lastKeywordSourcePosition = keywordToken.sourcePosition
        symbolValue += keywordToken.getStringValue()
        
        state, argument = parseAssociationExpression(state)
        arguments.append(argument)

    selector = ParseTreeLiteralSymbolNode(firstKeywordSourcePosition.to(lastKeywordSourcePosition), symbolValue)
    return state, ParseTreeMessageSendNode(state.sourcePositionFrom(startPosition), receiver, selector, arguments)

def parseLowPrecedenceExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.KEYWORD:
        return parseKeywordApplication(state)
    return parseKeywordMessageSend(state)

def parseAssignmentExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, assignedStore = parseLowPrecedenceExpression(state)
    if state.peekKind() == TokenKind.ASSIGNMENT:
        operatorToken = state.next()
        state, assignedValue = parseAssignmentExpression(state)
        return state, ParseTreeAssignmentNode(state.sourcePositionFrom(startPosition), assignedStore, assignedValue)
    else:
        return state, assignedStore

def parseCommaExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, element = parseAssignmentExpression(state)
    if state.peekKind() != TokenKind.COMMA:
        return state, element
    
    elements = [element]
    while state.peekKind() == TokenKind.COMMA:
        state.advance()
        state, element = parseAssignmentExpression(state)
        elements.append(element)
    
    return state, ParseTreeTupleNode(state.sourcePositionFrom(startPosition), elements)

def parseFunctionalType(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, argumentPatternOrExpression = parseCommaExpression(state)
    if state.peekKind() == TokenKind.COLON_COLON:
        state.advance()
        state, resultTypeExpression = parseFunctionalType(state)
        return state, ParseTreeFunctionalDependentTypeNode(state.sourcePositionFrom(startPosition), argumentPatternOrExpression, resultTypeExpression)
    return state, argumentPatternOrExpression

def parseFunctionalTypeWithOptionalArgument(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    if state.peekKind() == TokenKind.COLON_COLON:
        state.advance()
        startPosition = state.position
        state, resultTypeExpression = parseFunctionalType(state)
        return state, ParseTreeFunctionalDependentTypeNode(state.sourcePositionFrom(startPosition), None, resultTypeExpression)
    else:
        return parseFunctionalType(state)

def parseBindExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    startPosition = state.position
    state, patternExpressionOrValue = parseFunctionalTypeWithOptionalArgument(state)
    if state.peekKind() == TokenKind.BIND_OPERATOR:
        state.advance()
        state, boundValue = parseBindExpression(state)
        return state, ParseTreeBindPatternNode(state.sourcePositionFrom(startPosition), patternExpressionOrValue, boundValue)
    else:
        return state, patternExpressionOrValue

def parseExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    return parseBindExpression(state)

def parseExpressionListUntilEndOrDelimiter(state: ParserState, delimiter: TokenKind) -> tuple[ParserState, list[ParseTreeNode]]:
    elements = []

    # Chop the initial dots
    while state.peekKind() == TokenKind.DOT:
        state.advance()

    # Parse the next expression
    expectsExpression = True
    while not state.atEnd() and state.peekKind() != delimiter:
        if not expectsExpression:
            elements.append(ParseTreeErrorNode(state.currentSourcePosition(), "Expected dot before expression."))

        state, expression = parseExpression(state)
        elements.append(expression)

        expectsExpression = False
        # Chop the next dot sequence
        while state.peekKind() == TokenKind.DOT:
            expectsExpression = True
            state.advance()

    return state, elements

def parseSequenceUntilEndOrDelimiter(state: ParserState, delimiter: TokenKind) -> tuple[ParserState, ParseTreeNode]:
    initialPosition = state.position
    state, elements = parseExpressionListUntilEndOrDelimiter(state, delimiter)
    if len(elements) == 1:
        return state, elements[0]
    return state, ParseTreeSequenceNode(state.sourcePositionFrom(initialPosition), elements)

def parseTopLevelExpression(state: ParserState) -> tuple[ParserState, ParseTreeNode]:
    state, node = parseSequenceUntilEndOrDelimiter(state, TokenKind.END_OF_SOURCE)
    return node

def parseFileNamed(fileName: str) -> ParseTreeNode:
    sourceCode, tokens = scanFileNamed(fileName)
    state = ParserState(sourceCode, tokens)
    return parseTopLevelExpression(state)
    