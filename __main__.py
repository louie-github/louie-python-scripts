#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib
import sys

from pathlib import Path
from typing import List

# Add directory to path so we can import the scripts
sys.path.append(str(Path(__file__).parent))

from core import JSONArgumentParser  # noqa: E402

CLI_JSON_CONFIG_FILE = Path(__file__).parent / "cli" / f"{Path(__file__).stem}.json"


def run_module(module_name: str, args: List[str]):
    module = importlib.import_module(f"{module_name}")
    module.main(args)


parser = JSONArgumentParser(
    CLI_JSON_CONFIG_FILE, usage="louie [options] module [args...]"
)
args = parser.parse_args()
run_module(args.module, args.args)
