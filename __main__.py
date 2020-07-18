#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import importlib
import os
import sys

from typing import List


# Add directory to path so we can import the scripts
sys.path.append(os.path.dirname(__file__))


def run_module(module_name: str, args: List[str]):
    module = importlib.import_module(f"{module_name}")
    module.main(args)


parser = argparse.ArgumentParser(usage="louie [options] module [args...]")
parser.add_argument("module", help="The script to run.")
parser.add_argument(
    "args",
    help="The arguments to pass to the module's main function.",
    nargs=argparse.REMAINDER,
)
args = parser.parse_args()
run_module(args.module, args.args)
