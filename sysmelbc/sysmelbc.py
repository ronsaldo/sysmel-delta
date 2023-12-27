#!/usr/bin/env python3

import sysmel
import sys
import json

for arg in sys.argv[1:]:
    print(json.dumps(sysmel.parseFileNamed(arg).toJson()))

