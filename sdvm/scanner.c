#include "scanner.h"
#include <stdlib.h>
#include <string.h>

static const char *sdvm_tokenKindNameTable[] = {
#define SDVM_TOKEN_KIND_DEF(name) # name,
#include "token.inc"
#undef SDVM_TOKEN_KIND_DEF
};

const char *sdvm_scanner_getTokenKindName(sdvm_tokenKind_t kind)
{
    return sdvm_tokenKindNameTable[kind];
}

static sdvm_token_t sdvm_scanner_emptyToken(void)
{
    sdvm_token_t token = {0};
    return token;
}

static sdvm_token_t sdvm_scanner_tokenAtState(sdvm_scannerState_t *state, sdvm_tokenKind_t kind)
{
    sdvm_token_t token = {0};
    token.kind = kind;
    token.sourcePosition.sourceCollection = state->sourceCollection;
    token.sourcePosition.startIndex = token.sourcePosition.endIndex = state->position;
    token.sourcePosition.startLine = token.sourcePosition.endLine = state->line;
    token.sourcePosition.startColumn = token.sourcePosition.endColumn = state->column;
    return token;
}

static sdvm_token_t sdvm_scanner_errorTokenBetweenStates(sdvm_scannerState_t *startState, sdvm_scannerState_t *endState, const char *errorMessage)
{
    sdvm_token_t token = {0};
    token.kind = SdvmTokenKindError;
    token.message = errorMessage;
 
    token.sourcePosition.sourceCollection = startState->sourceCollection;
    token.sourcePosition.startIndex  = startState->position;
    token.sourcePosition.startLine   = startState->line;
    token.sourcePosition.startColumn = startState->column;

    token.sourcePosition.endIndex  = endState->position;
    token.sourcePosition.endLine   = endState->line;
    token.sourcePosition.endColumn = endState->column;
    return token;
}

static sdvm_token_t sdvm_scanner_tokenBetweenStates(sdvm_scannerState_t *startState, sdvm_scannerState_t *endState, sdvm_tokenKind_t kind)
{
    sdvm_token_t token = {0};
    token.kind = kind;
 
    token.sourcePosition.sourceCollection = startState->sourceCollection;
    token.sourcePosition.startIndex  = startState->position;
    token.sourcePosition.startLine   = startState->line;
    token.sourcePosition.startColumn = startState->column;

    token.sourcePosition.endIndex  = endState->position;
    token.sourcePosition.endLine   = endState->line;
    token.sourcePosition.endColumn = endState->column;
    return token;
}

sdvm_scannerState_t sdvm_scanner_initialize(sdvm_sourceCollection_t *sourceCollection)
{
    sdvm_scannerState_t state = {0};
    state.sourceCollection = sourceCollection;
    state.column = state.line = 1;
    return state;
}

static bool sdvm_scanner_atEnd(sdvm_scannerState_t *state)
{
    return state->position >= state->sourceCollection->sourceTextSize;
}

static int sdvm_scanner_lookAt(sdvm_scannerState_t *state, uint32_t offset)
{
    uint32_t lookPosition = state->position + offset;
    return lookPosition < state->sourceCollection->sourceTextSize ? state->sourceCollection->sourceText[lookPosition] : -1;
}

static void sdvm_scanner_advance(sdvm_scannerState_t *state)
{
    if(state->position >= state->sourceCollection->sourceTextSize)
        return;
    
    char c = state->sourceCollection->sourceText[state->position++];
    if(c == '\r')
    {
        ++state->line;
        state->column = 1;
        state->isPreviousCR = true;
    }
    else if(c == '\n')
    {
        if(!state->isPreviousCR)
        {
            ++state->line;
            state->column = 1;
        }
        state->isPreviousCR = false;
    }
    else if(c == '\t')
    {
        state->column = ((state->column + 4) / 4) * 4 + 1;
        state->isPreviousCR = false;
    }
    else
    {
        ++state->column;
        state->isPreviousCR = false;
    }
}

static void sdvm_scanner_advanceCount(sdvm_scannerState_t *state, int count)
{
    for(int i = 0; i < count; ++i)
        sdvm_scanner_advance(state);
}

static bool sdvm_scanner_isWhiteCharacter(int c)
{
    return 0 <= c && c <= ' ';
}

static void sdvm_scanner_skipWhite(sdvm_scannerState_t *state)
{
    while(sdvm_scanner_isWhiteCharacter(sdvm_scanner_lookAt(state, 0)))
        sdvm_scanner_advance(state);
}

static bool sdvm_scanner_isNewlineOrEndCharacter(int c)
{
    return c < 0 || c == '\r' || c == '\n';
}

static void sdvm_scanner_skipSingleLineComment(sdvm_scannerState_t *state)
{
    while(!sdvm_scanner_isNewlineOrEndCharacter(sdvm_scanner_lookAt(state, 0)))
        sdvm_scanner_advance(state);
}

static sdvm_token_t sdvm_scanner_skipMultiLineComment(sdvm_scannerState_t *state)
{
    if(sdvm_scanner_lookAt(state, 0) != '#' && sdvm_scanner_lookAt(state, 1) != '*')
        return sdvm_scanner_emptyToken();

    sdvm_scannerState_t startState = *state;
    sdvm_scanner_advanceCount(state, 2);

    while(!sdvm_scanner_atEnd(state))
    {
        if(sdvm_scanner_lookAt(state, 0) == '*' && sdvm_scanner_lookAt(state, 1) == '#')
        {
            sdvm_scanner_advanceCount(state, 2);
            return sdvm_scanner_emptyToken();
        }

        sdvm_scanner_advance(state);
    }

    return sdvm_scanner_errorTokenBetweenStates(&startState, state, "Incomplete multiline comment.");
}

static sdvm_token_t sdvm_scanner_skipWhiteAndComments(sdvm_scannerState_t *state)
{
    bool hasSeenComment = false;

    do
    {
        hasSeenComment = false;
        sdvm_scanner_skipWhite(state);

        // Skip the two types of different comments.
        if(sdvm_scanner_lookAt(state, 0) == '#')
        {
            int commentCharType = sdvm_scanner_lookAt(state, 1);
            if(commentCharType == '#')
            {
                sdvm_scanner_skipSingleLineComment(state);
                hasSeenComment = true;
            }
            else if(commentCharType == '*')
            {
                sdvm_token_t multiLineCommentError = sdvm_scanner_skipMultiLineComment(state);
                if(multiLineCommentError.kind)
                {
                    return multiLineCommentError;
                }
                hasSeenComment = true;
            }
        }
    } while(hasSeenComment);

    return sdvm_scanner_emptyToken();
}

static inline bool sdvm_scanner_isIdentifierStart(int c)
{
    return ('A' <= c && c <= 'Z') ||
        ('a' <= c && c <= 'z') ||
        '_' == c;
}

static inline bool sdvm_scanner_isAlpha(int c)
{
    return ('A' <= c && c <= 'Z') ||
        ('a' <= c && c <= 'z');
}

static inline bool sdvm_scanner_isDigit(int c)
{
    return '0' <= c && c <= '9';
}

static inline bool sdvm_scanner_isIdentifierMiddle(int c)
{
    return sdvm_scanner_isIdentifierStart(c) || sdvm_scanner_isDigit(c);
}

static inline bool sdvm_scanner_isDigitOrUnderscore(int c)
{
    return ('0' <= c && c <= '9') || c == '_';
}

static inline bool sdvm_scanner_isAlphanumericOrUnderscore(int c)
{
    return sdvm_scanner_isDigit(c) || sdvm_scanner_isAlpha(c) || c == '_';
}

static inline bool sdvm_scanner_isSign(int c)
{
    return '+' == c || c == '-';
}

static inline bool sdvm_scanner_isOperatorCharacter(int c)
{
    switch(c)
    {
    case '+':
    case '-':
    case '/':
    case '\\':
    case '*':
    case '~':
    case '<':
    case '>':
    case '=':
    case '@':
    case '%':
    case '|':
    case '&':
    case '?':
    case '!':
    case '^':
        return true;
    default:
        return false;
    }
}

static bool sdvm_scanner_advanceKeyword(sdvm_scannerState_t *state)
{
    if(!sdvm_scanner_isIdentifierStart(sdvm_scanner_lookAt(state, 0)))
        return false;

    sdvm_scannerState_t endState = *state;
    while(sdvm_scanner_isIdentifierMiddle(sdvm_scanner_lookAt(&endState, 0)))
        ++endState.position;

    if(sdvm_scanner_lookAt(&endState, 0) == ':')
    {
        ++endState.position;
        *state = endState;
        return true;
    }

    return false;
}

sdvm_token_t sdvm_scanner_nextToken(sdvm_scannerState_t *state)
{
    // Skip the whitespaces and the comments preceeding the token.
    {
        sdvm_token_t result = sdvm_scanner_skipWhiteAndComments(state);
        if(result.kind)
            return result;
    }

    // Is this the end?
    if(sdvm_scanner_atEnd(state))
        return sdvm_scanner_tokenAtState(state, SdvmTokenKindEndOfSource);

    sdvm_scannerState_t startState = *state;
    int c = sdvm_scanner_lookAt(state, 0);

    // Is this an identifier?
    if(sdvm_scanner_isIdentifierStart(c))
    {
        sdvm_scanner_advance(state);
        while(sdvm_scanner_isIdentifierMiddle(sdvm_scanner_lookAt(state, 0)))
            sdvm_scanner_advance(state);

        // Chop the scope resolutions.
        while(':' == sdvm_scanner_lookAt(state, 0) &&
            ':' == sdvm_scanner_lookAt(state, 1) &&
            sdvm_scanner_isIdentifierStart(sdvm_scanner_lookAt(state, 2)))
        {
            sdvm_scanner_advanceCount(state, 3);
            while(sdvm_scanner_isIdentifierMiddle(sdvm_scanner_lookAt(state, 0)))
                sdvm_scanner_advance(state);
        }

        // Operator with scope.
        if(':' == sdvm_scanner_lookAt(state, 0) &&
            ':' == sdvm_scanner_lookAt(state, 1) &&
            sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 2)))
        {
            sdvm_scanner_advanceCount(state, 3);
            while(sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 0)))
                sdvm_scanner_advance(state);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindOperator);
        }

        if(':' == sdvm_scanner_lookAt(state, 0))
        {
            sdvm_scanner_advance(state);

            bool isMultikeyword = false;
            while(sdvm_scanner_advanceKeyword(state))
                isMultikeyword = true;

            return sdvm_scanner_tokenBetweenStates(&startState, state, isMultikeyword ? SdvmTokenKindMultiKeyword : SdvmTokenKindKeyword);
        }

        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindIdentifier);
    }

    // Is this a number?
    if(sdvm_scanner_isDigit(c))
    {
        sdvm_scanner_advance(state);
        while(sdvm_scanner_isDigitOrUnderscore(sdvm_scanner_lookAt(state, 0)))
            sdvm_scanner_advance(state);

        // Did we parse the radix?
        if(sdvm_scanner_lookAt(state, 0) == 'r' || sdvm_scanner_lookAt(state, 0) == 'R')
        {
            sdvm_scanner_advance(state);
            while(sdvm_scanner_isAlphanumericOrUnderscore(sdvm_scanner_lookAt(state, 0)))
                sdvm_scanner_advance(state);

            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindInteger);
        }

        // Look for a float
        if(sdvm_scanner_lookAt(state, 0) == '.')
        {
            if(sdvm_scanner_isDigit(sdvm_scanner_lookAt(state, 1)) ||
                (sdvm_scanner_isSign(sdvm_scanner_lookAt(state, 1)) && sdvm_scanner_isDigit(sdvm_scanner_lookAt(state, 2))))
            {
                sdvm_scanner_advance(state); // Dot
                if(sdvm_scanner_isSign(sdvm_scanner_lookAt(state, 1)))
                    sdvm_scanner_advance(state); // sign
                sdvm_scanner_advance(state); // First decimal

                // Remaining fractional part
                while(sdvm_scanner_isDigitOrUnderscore(sdvm_scanner_lookAt(state, 0)))
                    sdvm_scanner_advance(state);

                // Exponent.
                if(sdvm_scanner_lookAt(state, 0) == 'e' || sdvm_scanner_lookAt(state, 0) == 'E')
                {
                    sdvm_scanner_advance(state);
                    if(sdvm_scanner_lookAt(state, 0) == '+' || sdvm_scanner_lookAt(state, 0) == '-')
                        sdvm_scanner_advance(state);

                    while(sdvm_scanner_isDigitOrUnderscore(sdvm_scanner_lookAt(state, 0)))
                        sdvm_scanner_advance(state);
                }

                return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindFloat);
            }
        }

        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindInteger);
    }

    // Strings
    if(c == '"')
    {
        sdvm_scanner_advance(state);
        while((c = sdvm_scanner_lookAt(state, 0)) != '"' && c >= 0)
        {
            if(c == '\\')
            {
                sdvm_scanner_advance(state);
                if(sdvm_scanner_atEnd(state))
                    return sdvm_scanner_errorTokenBetweenStates(&startState, state, "Incomplete string.");
            }
            sdvm_scanner_advance(state);
        }

        if(sdvm_scanner_lookAt(state, 0) != '"')
            return sdvm_scanner_errorTokenBetweenStates(&startState, state, "Incomplete string.");

        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindString);
    }
    
    // Characters
    if(c == '\'')
    {
        sdvm_scanner_advance(state);
        while((c = sdvm_scanner_lookAt(state, 0)) != '\'' && c >= 0)
        {
            if(c == '\\')
            {
                sdvm_scanner_advance(state);
                if(sdvm_scanner_atEnd(state))
                    return sdvm_scanner_errorTokenBetweenStates(&startState, state, "Incomplete character.");
            }
            sdvm_scanner_advance(state);
        }

        if(sdvm_scanner_lookAt(state, 0) != '\'')
            return sdvm_scanner_errorTokenBetweenStates(&startState, state, "Incomplete character.");

        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindCharacter);
    }

    if(c == '#')
    {
        int c1 = sdvm_scanner_lookAt(state, 1);

        // Identifier symbols
        if(sdvm_scanner_isIdentifierStart(c1))
        {
            sdvm_scanner_advanceCount(state, 2);
            while(sdvm_scanner_isIdentifierMiddle(sdvm_scanner_lookAt(state, 0)))
                sdvm_scanner_advance(state);

            // Chop the scope resolutions.
            while(':' == sdvm_scanner_lookAt(state, 0) &&
                ':' == sdvm_scanner_lookAt(state, 1) &&
                (sdvm_scanner_isIdentifierStart(sdvm_scanner_lookAt(state, 2))
                || sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 2)))
                )
            {
                sdvm_scanner_advanceCount(state, 2);
                if(sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 0)))
                {
                    while(sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 0)))
                        sdvm_scanner_advance(state);
                    return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindSymbol);
                }

                while(sdvm_scanner_isIdentifierMiddle(sdvm_scanner_lookAt(state, 0)))
                    sdvm_scanner_advance(state);
            }

            // Accept keyword symbols.
            if(':' == sdvm_scanner_lookAt(state, 0))
            {
                sdvm_scanner_advance(state);
                while(sdvm_scanner_advanceKeyword(state))
                    ;
            }

            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindSymbol);
        }

        // Operators
        if(sdvm_scanner_isOperatorCharacter(c1))
        {
            sdvm_scanner_advanceCount(state, 2);
            while(sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 0)))
                sdvm_scanner_advance(state);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindSymbol);
        }

        // String symbol
        if(c1 == '"')
        {
            sdvm_scanner_advanceCount(state, 2);
            while((c = sdvm_scanner_lookAt(state, 0)) != '"' && c >= 0)
            {
                if(c == '\\')
                {
                    sdvm_scanner_advance(state);
                    if(sdvm_scanner_atEnd(state))
                        return sdvm_scanner_errorTokenBetweenStates(&startState, state, "Incomplete string symbol.");
                }

                sdvm_scanner_advance(state);
            }

            if(sdvm_scanner_lookAt(state, 0) != '"')
                return sdvm_scanner_errorTokenBetweenStates(&startState, state, "Incomplete string symbol.");

            sdvm_scanner_advance(state);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindSymbol);
        }

        switch(c1)
        {
        case '[':
            sdvm_scanner_advanceCount(state, 2);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindByteArrayStart);
        case '{':
            sdvm_scanner_advanceCount(state, 2);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindDictionaryStart);
        case '(':
            sdvm_scanner_advanceCount(state, 2);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindLiteralArrayStart);
        default:
            break;
        }
    }
    
    switch(c)
    {
    case '(':
        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindLeftParent);
    case ')':
        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindRightParent);
    case '[':
        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindLeftBracket);
    case ']':
        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindRightBracket);
    case '{':
        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindLeftCurlyBracket);
    case '}':
        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindRightCurlyBracket);

    case ';':
        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindSemicolon);

    case ',':
        sdvm_scanner_advance(state);
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindComma);

    case '.':
        sdvm_scanner_advance(state);
        if('.' == sdvm_scanner_lookAt(state, 0) && '.' == sdvm_scanner_lookAt(state, 1))
        {
            sdvm_scanner_advanceCount(state, 2);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindEllipsis);
        }

        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindDot);
    case ':':
        sdvm_scanner_advance(state);
        if(':' == sdvm_scanner_lookAt(state, 0))
        {
            sdvm_scanner_advance(state);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindColonColon);
        }
        else if('=' == sdvm_scanner_lookAt(state, 0))
        {
            sdvm_scanner_advance(state);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindAssignment);
        }

        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindColon);

    case '`':
        {
            switch(sdvm_scanner_lookAt(state, 1))
            {
            case '\'':
                sdvm_scanner_advanceCount(state, 2);
                return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindQuote);
            case '`':
                sdvm_scanner_advanceCount(state, 2);
                return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindQuasiQuote);
            case ',':
                sdvm_scanner_advanceCount(state, 2);
                return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindQuasiUnquote);
            case '@':
                sdvm_scanner_advanceCount(state, 2);
                return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindSplice);
            default:
                break;
            }
        }
        break;
    case '|':
        sdvm_scanner_advance(state);
        if(sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 0)))
        {
            while(sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 0)))
                sdvm_scanner_advance(state);
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindOperator);
        }
        return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindBar);
    default:
        // Binary operators
        if(sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 0)))
        {
            while(sdvm_scanner_isOperatorCharacter(sdvm_scanner_lookAt(state, 0)))
                sdvm_scanner_advance(state);
            size_t operatorSize = state->position - startState.position;
            if(operatorSize == 1)
            {
                if(c == '<')
                    return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindLessThan);
                else if(c == '>')
                    return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindGreaterThan);
                else if(c == '*')
                    return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindStar);
            }
            
            return sdvm_scanner_tokenBetweenStates(&startState, state, SdvmTokenKindOperator);
        }
        break;
    }
    
    sdvm_scanner_advance(state);
    return sdvm_scanner_errorTokenBetweenStates(&startState, state, "Unexpected character");
}
