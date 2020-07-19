#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import os
import sys

from typing import List

# Add directory to path so we can import the scripts
sys.path.append(os.path.dirname(__file__))

# Import JSON argparse script
from core.json_argparse import JSONArgumentParser  # noqa: E402

json_file = os.path.join(os.path.dirname(__file__), "cli", "__main__.json")


def run_module(module_name: str, args: List[str]):
    module = importlib.import_module(f"{module_name}")
    module.main(args)


parser = JSONArgumentParser(json_file, usage="louie [options] module [args...]")
args = parser.parse_args()
run_module(args.module, args.args)
