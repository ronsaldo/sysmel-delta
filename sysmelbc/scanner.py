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
    def __init__(self, name, text):
        self.name = name
        self.text = text

    def __str__(self):
        return self.name

class SourcePosition:
    def __init__(self, sourceCode, startIndex, endIndex, startLine, startColumn, endLine, endColumn):
        self.sourceCode = sourceCode
        self.startIndex = startIndex
        self.endIndex = endIndex
        self.startLine = startLine
        self.startColumn = startColumn
        self.endLine = endLine
        self.endColumn = endColumn

    def __str__(self):
        return '%s:%d.%d-%d.%d' % (self.sourceCode, self.startLine, self.startColumn, self.endLine, self.endColumn)

class ScannerState:
    def __init__(self, sourceCode):
        self.sourceCode = sourceCode
        self.position = 0
        self.line = 1
        self.column = 1
        self.isPreviousCR = False
    
    def atEnd(self):
        return self.position >= len(self.sourceCode.text)

    def peek(self, peekOffset = 0):
        peekPosition = self.position + peekOffset
        if peekPosition < len(self.sourceCode.text):
            return self.sourceCode.text[peekPosition]
        else:
            return -1
        
    def advance(self):
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
        
    def makeToken(self, kind):
        sourcePosition = SourcePosition(self.sourceCode, self.position, self.position, self.line, self.column, self.line, self.column)
        return Token(kind, sourcePosition)

    def makeErrorToken(self, errorMessage):
        sourcePosition = SourcePosition(self.sourceCode, self.position, self.position, self.line, self.column, self.line, self.column)
        return Token(TokenKind.ERROR, sourcePosition, errorMessage)

class Token:
    def __init__(self, kind, sourcePosition, errorMessage=None):
        self.kind = kind
        self.sourcePosition = sourcePosition
        self.errorMessage = errorMessage

    def __repr__(self) -> str:
        if self.errorMessage is not None:
            return '%s: %s: %s' % (str(self.sourcePosition), repr(self.kind), self.errorMessage)
        else:
            return '%s: %s' % (str(self.sourcePosition), repr(self.kind))

def skipWhite(state):
    return state, None

def scanNextToken(state):
    state, whiteErrorToken = skipWhite(state)
    if whiteErrorToken is not None: return whiteErrorToken

    if state.atEnd():
        return state, state.makeToken(TokenKind.END_OF_SOURCE)
    
    initialState = copy.copy(state)
    c = state.peek()

    errorToken = state.makeErrorToken("Unexpected character " + repr(c))
    state.advance()
    return state, errorToken

def scanFileNamed(fileName):
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

        return tokens