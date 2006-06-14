#!/usr/bin/env python

from rasmus import util
import sys

words = util.readStrings(sys.argv[1])

if len(sys.argv[1:]) > 1:
    for fn in sys.argv[2:]:
        for line in file(fn):
            for word in words:
                if line.find(word) != -1:
                    print line,
                    break
else:
    for line in sys.stdin:
            for word in words:
                if line.find(word) != -1:
                    print line,
                    break
