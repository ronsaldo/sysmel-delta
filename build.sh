#!/bin/sh

OUT="build"
BIN="$OUT/bin"
OBJ="$OUT/obj"

set -ex
mkdir -p $BIN $OBJ

gcc -Wall -Wextra -g -O2 -I. -o $BIN/sdvm sdvm/sdvm.c
