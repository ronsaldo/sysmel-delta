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

sdvm_token_t sdvm_scanner_nextToken(sdvm_scannerState_t *state)
{
    // Skip the whitespaces and the comments preceeding the token.
    {
        sdvm_token_t result = sdvm_scanner_skipWhiteAndComments(state);
        if(result.kind)
            return result;
    }

    return sdvm_scanner_tokenAtState(state, SdvmTokenKindEndOfSource);
}
