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
    print(typechecked.prettyPrint())
    if not typecheckedSucceeded:
        sys.exit(1)

    evalResult = ASTEvaluator(FunctionalActivationEnvironment()).evaluate(typechecked)
    print(evalResult.prettyPrint())

# TODO: Compile the module.
    