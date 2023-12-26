#ifndef SDVM_AST_H
#define SDVM_AST_H

#include "rc.h"
#include "source.h"

typedef struct sdvm_astNode_s sdvm_astNode_t;

typedef enum sdvm_astNodeKind_e
{
#define AST_KIND(name) SdvmAstNodeKind ## name,
#include "astKind.inc"
#undef AST_KIND
} sdvm_astNodeKind_t;


typedef struct sdvm_astErrorNode_s
{
} sdvm_astErrorNode_t;

typedef struct sdvm_astIdentifierNode_s
{
} sdvm_astIdentifierNode_t;

typedef struct sdvm_astLiteralIntegerNode_s
{
} sdvm_astLiteralIntegerNode_t;

typedef struct sdvm_astLiteralFloatNode_s
{
} sdvm_astLiteralFloatNode_t;

struct sdvm_astNode_s
{
    sdvm_rc_t super;
    sdvm_sourcePosition_t sourcePosition;
    sdvm_astNodeKind_t kind;

    union
    {
        sdvm_astErrorNode_t error;
        sdvm_astIdentifierNode_t identifier;
        sdvm_astLiteralIntegerNode_t literalInteger;
        sdvm_astLiteralFloatNode_t literalFloat;
    };
} sdvm_astNode_t;

#endif //SDVM_AST_H
