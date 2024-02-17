#include "compiler.h"

void sdvm_compiler_x86_ret(sdvm_compiler_t *compiler)
{
    uint8_t instruction[] = {
        0xc3
    };

    sdvm_compiler_addInstruction(compiler, sizeof(instruction), instruction);
}

bool sdvm_compiler_x64_compileModuleFunction(sdvm_functionCompilationState_t *state)
{
    sdvm_compiler_t *compiler = state->compiler;

    sdvm_functionCompilationState_dump(state);

    sdvm_compiler_x86_ret(compiler);
    return true;
}
