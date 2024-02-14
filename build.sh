#!/bin/sh

OUT="build"
BIN="$OUT/bin"
OBJ="$OUT/obj"

set -ex
mkdir -p $BIN $OBJ

gcc -Wall -Wextra -g -I. -o $BIN/sdvm sdvm/sdvm-unity.c
