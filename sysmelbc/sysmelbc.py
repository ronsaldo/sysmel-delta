#!/usr/bin/env python3

from scanner import *
import sys

for arg in sys.argv[1:]:
    print(scanFileNamed(arg))

