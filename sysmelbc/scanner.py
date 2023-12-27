from enum import Enum
import copy

TokenKind = Enum('TokenKind', [
    'END_OF_SOURCE', 'ERROR',

    'CHARACTER', 'FLOAT', 'IDENTIFIER', 'INTEGER', 'KEYWORD', 'MULTI_KEYWORD', 'OPERATOR', 'STRING', 'SYMBOL',
    'LEFT_PARENT', 'RIGHT_PARENT', 'LEFT_BRACKET', 'RIGHT_BRACKET', 'LEFT_CURLY_BRACKET', 'RIGHT_CURLY_BRACKET',
    'LESS_THAN', 'GREATER_THAN', 'STAR',
    'COLON', 'COLON_COLON', 'BAR',
    'ASSIGNMENT', 'SEMICOLON', 'COMMA', 'DOT', 'ELLIPSIS',
    'QUOTE', 'QUASI_QUOTE', 'QUASI_UNQUOTE', 'SPLICE',
    'BYTE_ARRAY_START', 'DICTIONARY_START', 'LITERAL_ARRAY_START'
])

class SourceCode:
    def __init__(self, name: str, text: bytes) -> None:
        self.name = name
        self.text = text

    def __str__(self) -> str:
        return self.name

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

class Token:
    def __init__(self, kind: TokenKind, sourcePosition: SourcePosition, errorMessage: str = None):
        self.kind = kind
        self.sourcePosition = sourcePosition
        self.errorMessage = errorMessage

    def getValue(self) -> bytes:
        return self.sourcePosition.getValue()

    def getStringValue(self) -> str:
        return self.sourcePosition.getStringValue()

    def __repr__(self) -> str:
        if self.errorMessage is not None:
            return '%s: %s: %s' % (str(self.sourcePosition), repr(self.kind), self.errorMessage)
        else:
            return '%s: %s' % (str(self.sourcePosition), repr(self.kind))

class ScannerState:
    def __init__(self, sourceCode: SourceCode):
        self.sourceCode = sourceCode
        self.position = 0
        self.line = 1
        self.column = 1
        self.isPreviousCR = False
    
    def atEnd(self) -> bool:
        return self.position >= len(self.sourceCode.text)

    def peek(self, peekOffset: int = 0) -> int:
        peekPosition = self.position + peekOffset
        if peekPosition < len(self.sourceCode.text):
            return self.sourceCode.text[peekPosition]
        else:
            return -1
        
    def advance(self) -> None:
        assert self.position < len(self.sourceCode.text)
        c = self.sourceCode.text[self.position]
        self.position += 1
        if c == b'\r'[0]: 
            self.line += 1
            self.column = 1
            self.isPreviousCR = True
        elif c == b'\n'[0]: 
            if not self.isPreviousCR:
                self.line += 1
                self.column = 1
            self.isPreviousCR = False
        elif c == b'\t'[0]: 
            self.column = (self.column + 4) % 4 * 4 + 1
            self.isPreviousCR = False
        else:
            self.column += 1

    def advanceCount(self, count: int) -> None:
        for i in range(count):
            self.advance()
        
    def makeToken(self, kind: TokenKind) -> Token:
        sourcePosition = SourcePosition(self.sourceCode, self.position, self.position, self.line, self.column, self.line, self.column)
        return Token(kind, sourcePosition)
    
    def makeTokenStartingFrom(self, kind: TokenKind, initialState) -> Token:
        sourcePosition = SourcePosition(self.sourceCode, initialState.position, self.position, initialState.line, initialState.column, self.line, self.column)
        return Token(kind, sourcePosition)

    def makeErrorTokenStartingFrom(self, errorMessage: str, initialState):
        sourcePosition = SourcePosition(self.sourceCode, initialState.position, self.position, initialState.line, initialState.column, self.line, self.column)
        return Token(TokenKind.ERROR, sourcePosition, errorMessage)

def skipWhite(state: ScannerState) -> tuple[ScannerState, Token]:
    hasSeenComment = True
    while hasSeenComment:
        hasSeenComment = False
        while not state.atEnd() and state.peek() <= b' '[0]:
            state.advance()

        if state.peek() == b'#'[0]:
            if state.peek(1) == b'#'[0]:
                state.advanceCount(2)
                while not state.atEnd():
                    if state.peek() in b'\r\n':
                        break
                    state.advance()
                hasSeenComment = True

            elif state.peek(1) == b'*'[0]:
                commentInitialState = copy.copy(state)
                state.advanceCount(2)
                hasCommentEnd = False
                while not state.atEnd():
                    hasCommentEnd = state.peek() == b'*'[0] and state.peek(1) == b'#'[0]
                    if hasCommentEnd:
                        state.advanceCount(2)
                        break

                    state.advance()
                if not hasCommentEnd:
                    return state, state.makeErrorTokenStartingFrom('Incomplete multiline comment.', commentInitialState)

                hasSeenComment = True

    return state, None

def isDigit(c: int) -> bool:
    return (b'0'[0] <= c and c <= b'9'[0])

def isIdentifierStart(c: int) -> bool:
    return (b'A'[0] <= c and c <= b'Z'[0]) or \
        (b'a'[0] <= c and c <= b'z'[0]) or \
        (b'_'[0] == c)

def isIdentifierMiddle(c: int) -> bool:
    return isIdentifierStart(c) or isDigit(c)

def isOperatorCharacter(c: int) -> bool:
    return c >= 0 and c in b'+-/\\*~<>=@%|&?!^'

def scanAdvanceKeyword(state: ScannerState) -> tuple[ScannerState, Token]:
    if not isIdentifierStart(state.peek()):
        return state, False
    
    initialState = copy.copy(state)
    while isIdentifierMiddle(state.peek()):
        state.advance()

    if state.peek() != b':'[0]:
        return initialState, False

    state.advance()
    return state, True

def scanNextToken(state: ScannerState) -> tuple[ScannerState, Token]:
    state, whiteErrorToken = skipWhite(state)
    if whiteErrorToken is not None: return whiteErrorToken

    if state.atEnd():
        return state, state.makeToken(TokenKind.END_OF_SOURCE)
    
    initialState = copy.copy(state)
    c = state.peek()

    ## Identifiers, keywords and multi-keywords
    if isIdentifierStart(c):
        state.advance()
        while isIdentifierMiddle(state.peek()):
            state.advance()

        if state.peek() == b':'[0]:
            state.advance()
            isMultiKeyword = False
            hasAdvanced = True
            while hasAdvanced:
                state, hasAdvanced = scanAdvanceKeyword(state)
                isMultiKeyword = isMultiKeyword or hasAdvanced

            if isMultiKeyword:
                return state, state.makeTokenStartingFrom(TokenKind.MULTI_KEYWORD, initialState)
            else:
                return state, state.makeTokenStartingFrom(TokenKind.KEYWORD, initialState)
        
        return state, state.makeTokenStartingFrom(TokenKind.IDENTIFIER, initialState)
    
    ## Numbers
    if isDigit(c):
        state.advance()
        while isDigit(state.peek()):
            state.advance()

        ## Parse the radix.
        if not state.atEnd() and state.peek() in b'rR':
            state.advance()
            while isIdentifierMiddle(state.peek()):
                state.advance()
            return state, state.makeTokenStartingFrom(TokenKind.INTEGER, initialState)
        
        ## Decimal point.
        if state.peek() == b'.' and isDigit(state.peek(1)):
            state.advanceCount(2)
            while isDigit(state.peek()):
                state.advance()

            return state, state.makeTokenStartingFrom(TokenKind.FLOAT, initialState)
        
        return state, state.makeTokenStartingFrom(TokenKind.INTEGER, initialState)

    ## Symbols
    if c == b'#'[0]:
        c1 = state.peek(1)
        if isIdentifierStart(c1):
            state.advanceCount(2)
            while isIdentifierMiddle(state.peek()):
                state.advance()

            if state.peek() == b':'[0]:
                state.advance()
                isMultiKeyword = False
                hasAdvanced = True
                while hasAdvanced:
                    state, hasAdvanced = scanAdvanceKeyword(state)
                    isMultiKeyword = isMultiKeyword or hasAdvanced

                if isMultiKeyword:
                    return state, state.makeTokenStartingFrom(TokenKind.SYMBOL, initialState)
                else:
                    return state, state.makeTokenStartingFrom(TokenKind.SYMBOL, initialState)
            
            return state, state.makeTokenStartingFrom(TokenKind.SYMBOL, initialState)
        
        if c1 == b'['[0]:
            state.advanceCount(2)
            return state, state.makeTokenStartingFrom(TokenKind.BYTE_ARRAY_START, initialState)
        elif c1 == b'{'[0]:
            state.advanceCount(2)
            return state, state.makeTokenStartingFrom(TokenKind.DICTIONARY_START, initialState)
        elif c1 == b'('[0]:
            state.advanceCount(2)
            return state, state.makeTokenStartingFrom(TokenKind.LITERAL_ARRAY_START, initialState)

    ## Strings
    if c == b'"'[0]:
        state.advance()
        while not state.atEnd() and state.peek() != b'"'[0]:
            if state.peek() == b'\\'[0] and state.peek(1) >= 0:
                state.advanceCount(2)
            else:
                state.advance()

        if state.peek() != b'"'[0]:
            return state, state.makeErrorTokenStartingFrom("Incomplete string literal.", initialState)
        state.advance()

        return state, state.makeTokenStartingFrom(TokenKind.STRING, initialState)

    ## Characters
    if c == b"'"[0]:
        state.advance()
        while not state.atEnd() and state.peek() != b"'"[0]:
            if state.peek() == b'\\'[0] and state.peek(1) >= 0:
                state.advanceCount(2)
            else:
                state.advance() 
        if state.peek() != b"'"[0]:
            return state, state.makeErrorTokenStartingFrom("Incomplete character literal.", initialState)
        state.advance()

        return state, state.makeTokenStartingFrom(TokenKind.CHARACTER, initialState)

    if c == b'('[0]:
        state.advance()
        return state, state.makeTokenStartingFrom(TokenKind.LEFT_PARENT, initialState)
    elif c == b')'[0]:
        state.advance()
        return state, state.makeTokenStartingFrom(TokenKind.RIGHT_PARENT, initialState)
    elif c == b'['[0]:
        state.advance()
        return state, state.makeTokenStartingFrom(TokenKind.LEFT_BRACKET, initialState)
    elif c == b']'[0]:
        state.advance()
        return state, state.makeTokenStartingFrom(TokenKind.RIGHT_BRACKET, initialState)
    elif c == b'{'[0]:
        state.advance()
        return state, state.makeTokenStartingFrom(TokenKind.LEFT_CURLY_BRACKET, initialState)
    elif c == b'}'[0]:
        state.advance()
        return state, state.makeTokenStartingFrom(TokenKind.RIGHT_CURLY_BRACKET, initialState)
    elif c == b';'[0]:
        state.advance()
        return state, state.makeTokenStartingFrom(TokenKind.SEMICOLON, initialState)
    elif c == b','[0]:
        state.advance()
        return state, state.makeTokenStartingFrom(TokenKind.COMMA, initialState)
    elif c == b'.'[0]:
        state.advance()
        if state.peek(0) == b'.'[0] and state.peek(1) == b'.'[0]:
            state.advanceCount(2)
            return state, state.makeTokenStartingFrom(TokenKind.ELLIPSIS, initialState)
        return state, state.makeTokenStartingFrom(TokenKind.DOT, initialState)
    elif c == b':'[0]:
        state.advance()
        if state.peek(0) == b':'[0]:
            state.advance()
            return state, state.makeTokenStartingFrom(TokenKind.COLON_COLON, initialState)
        elif state.peek(0) == b'='[0]:
            state.advance()
            return state, state.makeTokenStartingFrom(TokenKind.ASSIGNMENT, initialState)
        return state, state.makeTokenStartingFrom(TokenKind.COLON, initialState)
    elif c == b'`'[0]:
        if state.peek(1) == b'\''[0]:
            state.advance()
            return state, state.makeTokenStartingFrom(TokenKind.QUOTE, initialState)
        elif state.peek(1) == b'`'[0]:
            state.advance()
            return state, state.makeTokenStartingFrom(TokenKind.QUASI_QUOTE, initialState)
        elif state.peek(1) == b','[0]:
            state.advance()
            return state, state.makeTokenStartingFrom(TokenKind.QUASI_UNQUOTE, initialState)
        elif state.peek(1) == b'@'[0]:
            state.advance()
            return state, state.makeTokenStartingFrom(TokenKind.SPLICE, initialState)
    elif c == b'|'[0]:
        state.advance()
        if isOperatorCharacter(state.peek()):
            while isOperatorCharacter(state.peek()):
                state.advance()
            return state, state.makeTokenStartingFrom(TokenKind.OPERATOR, initialState)
        return state, state.makeTokenStartingFrom(TokenKind.BAR, initialState)
    elif isOperatorCharacter(c):
        while isOperatorCharacter(state.peek()):
            state.advance()
        token = state.makeTokenStartingFrom(TokenKind.OPERATOR, initialState)
        tokenValue = token.getValue()
        if tokenValue == b'<':
            token.kind = TokenKind.LESS_THAN
        elif tokenValue == b'>':
            token.kind = TokenKind.GREATER_THAN
        elif tokenValue == b'*':
            token.kind = TokenKind.STAR
        return state, token

    state.advance()
    errorToken = state.makeErrorTokenStartingFrom("Unexpected character.", initialState)
    return state, errorToken

def scanFileNamed(fileName: str) -> tuple[SourceCode, list[Token]]:
    with open(fileName, "rb") as f:
        sourceText = f.read()
        sourceCode = SourceCode(fileName, sourceText)
        state = ScannerState(sourceCode)
        tokens = []
        while True:
            state, token = scanNextToken(state)
            tokens.append(token)
            if token.kind == TokenKind.END_OF_SOURCE:
                break

        return sourceCode, tokens
