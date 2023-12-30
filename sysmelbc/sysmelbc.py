#!/usr/bin/env python3

import sysmel
import sys
import json

for arg in sys.argv[1:]:
    ast = sysmel.parseFileNamed(arg)
    if not sysmel.ASTErrorVisitor().checkASTAndPrintErrors(ast):
        sys.exit(1)

    typechecked = sysmel.Typechecker().typecheckASTAndPrintErrors(ast)
    print(json.dumps(typechecked.toJson()))

    evalResult = sysmel.ASTEvaluator().evaluate(typechecked)
    print(json.dumps(evalResult.toJson()))

