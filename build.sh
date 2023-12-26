#!/bin/sh

OUT="build"
BIN="$OUT/bin"
OBJ="$OUT/obj"

set -ex
mkdir -p $BIN $OBJ

## Build the bootstrap compiler.
ghc -o build/bin/sysmelbc -odir build/obj/sysmelbc -hidir build/obj/sysmelbc -isysmelbc --make sysmelbc/sysmelbc.hs

##gcc -Wall -Wextra -g -O2 -I. -o $BIN/sdvm sdvm/sdvm.c
##gcc -Wall -Wextra -g -O2 -I. -o $BIN/sdvm-as sdvm/sdvm-as.c sdvm/ast.c sdvm/parser.c sdvm/rc.c sdvm/scanner.c sdvm/source.c

