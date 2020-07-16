#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import shlex
import subprocess
import sys

_PY_LAUNCHER_COMMAND = ["py", "-3.8", "-m"]
PIP_LIST_COMMAND = ["pip", "list"]
PIP_UPGRADE_COMMAND = ["pip", "install", "--upgrade", "--no-cache-dir"]
PIP_LIST_REGEX = re.compile(r"([\S]*) *(.*)")


def get_packages(cmd=PIP_LIST_COMMAND, regex=PIP_LIST_REGEX):
    sys_encoding = sys.stdout.encoding
    output = subprocess.check_output(cmd)
    # Parse output into a list of lines and decode into str; strip
    lines = [line.decode(sys_encoding).strip() for line in output.splitlines()]
    # Check if output has the expected prefix lines
    if not lines[:2] == ["Package           Version", "----------------- ---------"]:
        return
    # Skip first two lines
    for line in lines[2:]:
        match = regex.match(line)
        if match:
            yield match.group(1)


def generate_upgrade_command(packages, prefix=PIP_UPGRADE_COMMAND):
    # Quote every package for safety, if needed
    packages_str = " ".join([shlex.quote(package) for package in packages])
    prefix = shlex.join(prefix)
    return f"{prefix} {packages_str}"


if __name__ == "__main__":
    # Ignore duplicate imports
    import argparse, sys  # noqa

    parser = argparse.ArgumentParser(
        description="Generate a command to update all installed pip packages"
    )
    parser.add_argument(
        "--prefix",
        help=(
            "If specified, the command to prefix before all pip <command> strings.\n"
            "Overrides --use_py if specified. Example: --prefix 'python -m'"
        ),
        default=None,
        metavar="COMMAND",
        dest="prefix",
    )
    parser.add_argument(
        "--use-py",
        help="Use py launcher (Windows only, ignored otherwise)",
        action="store_true",
        default=True,  # We will disable this later if not on Windows
        dest="use_py",
    )
    args = parser.parse_args()
    # Define base commands
    pip_list_command = PIP_LIST_COMMAND
    pip_upgrade_command = PIP_UPGRADE_COMMAND
    # Remove use_py argument if not running on Windows
    if sys.platform != "win32":
        args.use_py = False
    # Override py launcher with prefix
    if args.prefix:
        args.use_py = False
    # Append py launcher / prefixes if necessary
    if args.use_py:
        pip_list_command = _PY_LAUNCHER_COMMAND + pip_list_command
        pip_upgrade_command = _PY_LAUNCHER_COMMAND + pip_upgrade_command
    elif args.prefix:
        prefix = shlex.split(args.prefix)
        pip_list_command = prefix + pip_list_command
        pip_upgrade_command = prefix + pip_upgrade_command
    # Main code
    packages = get_packages(cmd=pip_list_command)
    print(generate_upgrade_command(packages, prefix=pip_upgrade_command))
