#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a command to upgrade all installed pip packages.

Usage:
    pipup [--quiet | --verbose] [options]
    pipup [--help | --version]

Options:
    --help       Print this help message and exit.
    --version    Print the current version of the script.

Output options:
    -v, --verbose    Print verbose output (useful for debugging.)
    -q, --quiet      Suppress the output of subprocess calls, i.e. quiet mode.
                     Note: This is currently unused; either the output command string
                     or '--run' will always output to stdout.

Script options:
    -r, --run             Run the resulting command instead of printing it. (DANGEROUS)
    --outdated            List only the outdated packages by adding '--outdated' to 'pip list'.
    --skip-checks         Skip checking the output of the 'pip list' command and parse it directly.
    -n, --no-cache-dir    Append '--no-cache-dir' to the pip upgrade command.

Python launcher options:
    -c, --prefix <command>            The prefix to add before each 'pip' command. Overrides the py launcher
                                      when using Windows. Default is to base it off of '--python-version'.
                                      (Example: 'python3.8 -m' on Unix and 'py -3.8' on Windows.)
    -p, --python-version <version>    The version of Python to use when calling 'pip'. [default: 3]

"""

import argparse
import re
import shlex
import string
import subprocess
import sys

from collections import deque
from typing import Iterable, List


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


# Standard argument parsing API
def create_parser():
    parser = argparse.ArgumentParser(
        prog="pipup",
        usage="pipup [--quiet | --verbose] [options]",
        description="Generate a command to upgrade all installed pip packages.",
    )
    output_options = parser.add_mutually_exclusive_group()
    output_options.add_argument(
        "-v",
        "--verbose",
        help="enable verbose output (useful for debugging)",
        action="store_true",
        dest="verbose",
    )
    output_options.add_argument(
        "-q",
        "--quiet",
        help="suppress output (currently unused; '--run' will always output)",
        action="store_true",
        dest="quiet",
    )
    script_options = parser.add_argument_group(title="script options")
    script_options.add_argument(
        "-r",
        "--run",
        help="run the output command instead of printing it (not recommended)",
        action="store_true",
        dest="run",
    )
    script_options.add_argument(
        "-o",
        "--outdated",
        help="only list the outdated packages",
        action="store_true",
        dest="outdated",
    )
    script_options.add_argument(
        "--skip-checks",
        help="skip checking the output of the 'pip list' command and parse it directly",
        action="store_true",
        dest="skip_checks",
    )
    script_options.add_argument(
        "-n",
        "--no-cache-dir",
        action="store_true",
        help="append '--no-cache-dir' to the 'pip upgrade' command",
        dest="no_cache_dir",
    )
    python_options = parser.add_argument_group(title="Python launcher options")
    python_options.add_argument(
        "-c",
        "--prefix",
        help="\n".join(
            [
                "prepend COMMAND before each 'pip' command.\n",
                "(defaults to 'py -[version] -m' on Windows and 'python[version] -m' on Unix.",
            ]
        ),
        metavar="COMMAND",
        nargs="?",
        default=None,
        dest="prefix",
    )
    python_options.add_argument(
        "-p",
        "--python-version",
        help="the version of Python to use [default: 3]",
        metavar="VERSION",
        nargs="?",
        default="3",
        dest="python_version",
    )
    python_options.add_argument(
        "--no-py",
        "--no-py-launcher",
        help="disable using the 'py' launcher on Windows",
        action="store_false",
        dest="use_py",
    )
    return parser


def configure(args: argparse.Namespace):
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
