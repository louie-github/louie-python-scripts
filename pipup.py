#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2020 louie-github
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Usage: pipup [--quiet | --verbose] [options]

Generate a command to upgrade all installed pip packages.

Optional arguments:
  -h, --help                show this help message and exit
  -v, --verbose             enable verbose output (useful for debugging)
  -q, --quiet               suppress output (currently unused; '--run' will always output)

Script options:
  -r, --run                 run the output command instead of printing it (not recommended)
  -o, --outdated            only list the outdated packages
  --skip-checks             skip checking the output of the 'pip list' command and parse it directly
  -n, --no-cache-dir        append '--no-cache-dir' to the 'pip upgrade' command

Python launcher options:
  -c, --prefix [COMMAND]    add the prefix COMMAND before each 'pip' command
                            [default: 'py -[version] -m' on Windows, 'python[version] -m' on Unix]
  -p, --python [VERSION]    the version of Python to use [default: 3]
  --no-py[-launcher]        disable using the 'py' launcher on Windows
"""

import argparse
import re
import shlex
import string
import subprocess
import sys

from collections import deque
from pathlib import Path
from typing import Iterable, List

from core import JSONArgumentParser

CLI_JSON_CONFIG_FILE = Path(__file__).parent / "cli" / f"{Path(__file__).stem}.json"

__all__ = ["get_packages", "generate_upgrade_command"]

PY_LAUNCHER_COMMAND = ["py", "<python-version>", "-m"]
PYTHON_COMMAND = ["python"]
PIP_LIST_COMMAND = ["pip", "list"]
PIP_UPGRADE_COMMAND = ["pip", "install", "--upgrade"]
PIP_LIST_REGEX = re.compile(r"([\S]*) *(.*)")


# Support for Python <3.8
try:
    shlex.join(["ignore", "this", "command"])
except AttributeError:

    def _shlex_join(split_command):
        """Return a shell-escaped string from *split_command*."""
        return " ".join(shlex.quote(arg) for arg in split_command)

    shlex.join = _shlex_join

# By default, verbose printing is off.
vprint = lambda *args, **kwargs: None  # noqa E731

# Regular printing is on.
rprint = print


def _remove_whitespace(text, whitespace=string.whitespace):
    # Could also be text.translate(str.maketrans('', '', whitespace)
    return "".join(c for c in text if c not in whitespace)


def _check_pip_list_prefix(lines):
    prefix_lines = lines[:2]
    checks = [
        # 1. Check that the first line contains the words 'Package' and 'Version'
        _remove_whitespace(prefix_lines[0]) == "PackageVersion",
        # 2. Check that the second line contains only dashes
        set(_remove_whitespace(prefix_lines[1])) == {"-"},
    ]
    return all(checks), prefix_lines


def get_packages(
    list_command=PIP_LIST_COMMAND, regex=PIP_LIST_REGEX, skip_checks=False
):
    sys_encoding = sys.stdout.encoding
    vprint(f"Running 'pip list' command: {list_command}")
    output = subprocess.check_output(list_command)
    if not output:
        return
    # Parse output into a list of lines and decode into str
    # (also strip whitespace)
    lines = [line.decode(sys_encoding).strip() for line in output.splitlines()]
    # Check if output has the expected prefix lines
    if not skip_checks:
        passed, checked_lines = _check_pip_list_prefix(lines)
        vprint(f"Passed 'pip list' output checks on lines: {checked_lines}")
        if not passed:
            raise ValueError(
                f"Expected a valid 'pip list' output, instead got: {checked_lines}"
            )
    else:
        vprint("Skipped 'pip list' output checks.")
    # Skip first two lines
    for line in lines[2:]:
        match = regex.match(line)
        if match:
            yield match.group(1)


def generate_upgrade_command(
    packages: Iterable = None,
    upgrade_command: Iterable = PIP_UPGRADE_COMMAND,
    join_output: bool = False,
    *args,
    **kwargs,
):
    # Get packages if not specified
    packages = packages if packages is not None else get_packages(*args, **kwargs)
    packages = list(packages)
    vprint(f"Found packages: {packages}")
    output = list(upgrade_command) + packages
    if join_output:
        return shlex.join(output)
    else:
        return output


# Create help command override
class DocstringHelp(argparse.Action):
    def __call__(self, *args, **kwargs):
        print(__doc__)
        raise SystemExit


# Standard argument parsing API
def create_parser():
    parser = JSONArgumentParser(CLI_JSON_CONFIG_FILE)
    # Override help command
    parser.add_argument(
        "-h",
        "--help",
        help="show this help message and exit",
        nargs=0,
        action=DocstringHelp,
    )
    return parser


def configure(args: argparse.Namespace):
    # Manually define help command behavior
    if args.help:
        print(__doc__)
        raise SystemExit
    global rprint, vprint

    if args.verbose:

        def vprint(text, *args, **kwargs):
            print(f"[DEBUG] {text}")

    elif args.quiet:
        rprint = vprint = lambda *args, **kwargs: None

    vprint(f"Parsed arguments: {args}")

    # Define base commands
    pip_list_command = deque(PIP_LIST_COMMAND)
    pip_upgrade_command = deque(PIP_UPGRADE_COMMAND)

    # Main argument parsing
    is_windows = sys.platform.startswith("win32")
    python_version = args.python_version.strip()
    # Apply prefixes in order of: args.prefix, Windows py launcher, python[version]
    if args.prefix is not None:
        prefix = shlex.split(args.prefix)
    elif is_windows:
        if args.use_py:
            prefix = PY_LAUNCHER_COMMAND.copy()
            prefix[prefix.index("<python-version>")] = f"-{python_version}"
        else:
            prefix = ["python", "-m"]
    else:
        prefix = [f"python{python_version}", "-m"]

    # Add prefix to all commands
    pip_list_command.extendleft(reversed(prefix))
    pip_upgrade_command.extendleft(reversed(prefix))

    # Add extra flags to pip commands if necessary
    if args.outdated:
        pip_list_command.append("--outdated")
    if args.no_cache_dir:
        pip_upgrade_command.append("--no-cache-dir")

    return pip_list_command, pip_upgrade_command


# ----- INTERACTIVE CODE ----
def main(args: List[str] = None):
    # Parse arguments
    parser = create_parser()
    if args is not None:
        parsed_args = parser.parse_args(args)
    else:
        parsed_args = parser.parse_args()

    # Configure commands based on parsed args
    pip_list_command, pip_upgrade_command = configure(parsed_args)
    vprint(f"pip_list_command: {pip_list_command}")
    vprint(f"pip_upgrade_command: {pip_upgrade_command}")

    # Main code
    packages = get_packages(list_command=pip_list_command)
    packages = list(packages)
    if not packages:
        if parsed_args.outdated:
            rprint("All packages are up to date. Exiting normally.")
        else:
            vprint(
                "'pip list' returned an empty output and the --outdated flag was not specified."
            )
            vprint("Exiting normally.")
        raise SystemExit
    if parsed_args.run:
        command = generate_upgrade_command(
            packages, upgrade_command=pip_upgrade_command, join_output=False
        )
        subprocess.run(command)
    else:
        command = generate_upgrade_command(
            packages, upgrade_command=pip_upgrade_command, join_output=True
        )
        print(command)


if __name__ == "__main__":
    main()
