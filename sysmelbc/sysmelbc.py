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
print(ghirModule.prettyPrint())

# Compile the HIR module.
hirModule = HIRModuleFrontend().compileGraphModule(ghirModule)
print(hirModule.prettyPrint())

# Compile the sdvm module
sdvmModule = SDVMModuleFrontEnd().compileGHIRModule(ghirModule)
print(sdvmModule.prettyPrint())
sdvmModule.saveToFileNamed("test.sdvm")

