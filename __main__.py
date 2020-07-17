#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import importlib
import os
import sys

from typing import List


def run_module(module_name: str, args: List[str]):
    module = importlib.import_module(f".{module_name}", "WHY")
    module.main(args)


parser = argparse.ArgumentParser()
parser.add_argument("module", help="The script to run.")
parser.add_argument(
    "args", help="The arguments to pass to the module's main function.", nargs="*",
)

# Use a copy of sys.argv when modifying it
argv = sys.argv.copy()
argv.pop(0)
# Find the first positional argument
for index, arg in enumerate(argv):
    if not arg.startswith("-"):
        first_pos = index
        add_dash = True
        break
else:
    add_dash = False
# Recreate docopt 'options_first' by adding '--' before the first positional
if add_dash:
    argv = [*(argv[:first_pos]), "--", *(argv[first_pos:])]
print(argv)
# Use edited sys.argv
args = parser.parse_args(argv)
print(args)
run_module(args.module, args.args)
