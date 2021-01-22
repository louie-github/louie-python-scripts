#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


# Add shlex.join functionality for Python <3.8
try:
    shlex.join(["command"])
except AttributeError:

    # Copy code from Python 3.8
    def _shlex_join(split_command):
        """Return a shell-escaped string from *split_command*."""
        return " ".join(shlex.quote(arg) for arg in split_command)

    shlex.join = _shlex_join


def no_print(*args, **kwargs):
    pass


def debug_print(text=None, **kwargs):
    # Do not add debug prefix if string is empty or not given
    # Emulate behavior of print() [vprint() == print()]
    if not text:
        print(**kwargs)
    else:
        print(f"[DEBUG] {text}")


def _remove_whitespace(text, whitespace=string.whitespace):
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
    list_command: Iterable = PIP_LIST_COMMAND,
    regex: Iterable = PIP_LIST_REGEX,
    skip_checks=False,
):
    sys_encoding = sys.stdout.encoding
    vprint(f"Running 'pip list' command: {list_command}")
    output = subprocess.check_output(list_command)
    if not output:
        return
    # Parse output into a list of lines
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
    # Ignore prefix lines when matching
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


def create_parser():
    return JSONArgumentParser(CLI_JSON_CONFIG_FILE)


def configure(args: argparse.Namespace):
    global rprint, vprint

    # By default, verbose printing is off and regular message printing is on.
    rprint = print
    vprint = no_print

    if args.verbose:
        vprint = debug_print

    elif args.quiet:
        rprint = no_print
        vprint = no_print

    vprint(f"Parsed arguments: {args}")

    # Define base commands
    pip_list_command = deque(PIP_LIST_COMMAND)
    pip_upgrade_command = deque(PIP_UPGRADE_COMMAND)

    # Create command prefix
    is_windows = sys.platform.startswith("win32")
    python_version = args.python_version.strip()

    # Custom prefix: read prefix from command line arguments
    if args.prefix is not None:
        prefix = shlex.split(args.prefix)
    # Windows: Use py launcher by default, fall back to "python" command
    elif is_windows:
        if args.use_py:
            prefix = PY_LAUNCHER_COMMAND.copy()
            # Replace the "<python-version>" placeholder with the actual
            # installed Python version string
            prefix[prefix.index("<python-version>")] = f"-{python_version}"
        else:
            prefix = ["python", "-m"]
    # Unix / other systems: Use python[version] format command
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
    packages = list(get_packages(list_command=pip_list_command))
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
        vprint()
        print(command)


if __name__ == "__main__":
    main()
