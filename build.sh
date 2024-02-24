#!/bin/sh

OUT="build"
BIN="$OUT/bin"
OBJ="$OUT/obj"

set -ex
mkdir -p $BIN $OBJ

gcc -Wall -Wextra -Wno-unknown-pragmas -g -I. -o $BIN/sdvm sdvm/sdvm-unity.c
