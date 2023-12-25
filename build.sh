#!/bin/sh

OUT="build"

set -ex
mkdir -p $OUT
gcc -Wall -Wextra -g -O2 -I. -o $OUT/sdvm sdvm/sdvm.c
gcc -Wall -Wextra -g -O2 -I. -o $OUT/sdvm-as sdvm/sdvm-as.c sdvm/ast.c sdvm/parser.c sdvm/rc.c sdvm/scanner.c sdvm/source.c
