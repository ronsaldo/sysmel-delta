#!/usr/bin/env python3

from sysmel import *
import sys
import json
import os.path

module = None
# Evaluate the command line arguments
for arg in sys.argv[1:]:
    if module is None:
        moduleName, ext = os.path.splitext(os.path.basename(arg))
        module = Module(Symbol.intern(moduleName))

    ast = parseFileNamed(arg)
    if not ASTErrorVisitor().checkASTAndPrintErrors(ast):
        sys.exit(1)

    typechecked, typecheckedSucceeded = Typechecker(makeScriptAnalysisEnvironment(module, ast.sourcePosition, arg)).typecheckASTAndPrintErrors(ast)
    ##print(json.dumps(typechecked.toJson()))
    ##print(typechecked.prettyPrint())
    if not typecheckedSucceeded:
        sys.exit(1)

    evalResult = ASTEvaluator(FunctionalActivationEnvironment()).evaluate(typechecked)
    print(evalResult.prettyPrint())

# Compile the Graph HIR module.
ghirModule = GHIRModuleFrontend().compileModule(module)
print('-'*60)
print('GHIR:')
print('-'*60)
print(ghirModule.prettyPrint())

# Compile the HIR module.
hirModule = HIRModuleFrontend().compileGraphModule(ghirModule)

print('-'*60)
print('HIR:')
print('-'*60)
print(hirModule.prettyPrint())

# Compile the MIR module.
mirModule = MIRModuleFrontend().compileHIRModule(hirModule)

print('-'*60)
print('MIR:')
print('-'*60)
print(mirModule.prettyPrint())

# Compile the SDVM module
sdvmModule = SDVMModuleFrontEnd().compileMIRModule(mirModule)

print('-'*60)
print('SDVM:')
print('-'*60)
print(sdvmModule.prettyPrint())
sdvmModule.saveToFileNamed("test.sdvm")

