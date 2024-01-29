#!/usr/bin/env python3

from sysmel import *
import sys
import json

for arg in sys.argv[1:]:
    ast = parseFileNamed(arg)
    if not ASTErrorVisitor().checkASTAndPrintErrors(ast):
        sys.exit(1)

    typechecked, typecheckedSucceeded = Typechecker(makeDefaultEvaluationEnvironment()).typecheckASTAndPrintErrors(ast)
    print(json.dumps(typechecked.toJson()))
    if not typecheckedSucceeded:
        sys.exit(1)

    evalResult = ASTEvaluator(FunctionalActivationEnvironment()).evaluate(typechecked)
    print(json.dumps(evalResult.toJson()))

