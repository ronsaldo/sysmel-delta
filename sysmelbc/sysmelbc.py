#!/usr/bin/env python3

import sysmel
import sys
import json

for arg in sys.argv[1:]:
    ast = sysmel.parseFileNamed(arg)
    if not sysmel.ASTErrorVisitor().checkASTAndPrintErrors(ast):
        sys.exit(1)

    typechecked, typecheckedSucceeded = sysmel.Typechecker(sysmel.makeDefaultEvaluationEnvironment()).typecheckASTAndPrintErrors(ast)
    print(json.dumps(typechecked.toJson()))
    if not typecheckedSucceeded:
        sys.exit(1)

    evalResult = sysmel.ASTEvaluator().evaluate(typechecked)
    print(json.dumps(evalResult.toJson()))

