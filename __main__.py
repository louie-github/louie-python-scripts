#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import importlib

from typing import List


def run_module(module_name: str, args: List[str]):
    module = importlib.import_module(module_name)
    module.main(args)


parser = argparse.ArgumentParser()
parser.add_argument("module", help="The script to run.")
parser.add_argument(
    "args", help="The arguments to pass to the module's main function.", nargs="*",
)
args = parser.parse_args()
run_module(args.module, args.args)
