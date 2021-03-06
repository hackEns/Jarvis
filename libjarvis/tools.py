#!/usr/bin/env python3

"""
Misc functions.
"""

import sys


def warning(*objs):
    """Write warnings to stderr"""
    print("WARNING: ", *objs, file=sys.stderr)
