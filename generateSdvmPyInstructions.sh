#!/bin/sh

set -ex
gcc -Wall -Wextra -g -O2 -I. -o sdvmPyInstructions.exe sdvm/sdvm-py-instructions.c && ./sdvmPyInstructions.exe > sysmelbc/sysmel/sdvmInstructions.py
