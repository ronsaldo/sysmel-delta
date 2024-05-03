#!/bin/sh

OUT="build"
BIN="$OUT/bin"
OBJ="$OUT/obj"

set -ex
mkdir -p $BIN $OBJ

clang -Wall -Wextra -Wno-unknown-pragmas -g -I. -o $BIN/sdvm sdvm/sdvm-unity.c
