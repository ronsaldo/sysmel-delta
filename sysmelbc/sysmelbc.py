#!/usr/bin/env python3

from sparser import parseFileNamed
import sys
import json

for arg in sys.argv[1:]:
    print(json.dumps(parseFileNamed(arg).toJson()))

