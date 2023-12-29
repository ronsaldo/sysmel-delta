#!/usr/bin/env python3

import sysmel
import sys
import json

for arg in sys.argv[1:]:
    ast = sysmel.parseFileNamed(arg)
    if not sysmel.ASTErrorVisitor().checkASTAndPrintErrors(ast):
        sys.exit(1)
    ##print(json.dumps(ast.toJson()))

    evalResult = sysmel.ASTEvaluator().evaluate(ast)
    print(json.dumps(evalResult.toJson()))

