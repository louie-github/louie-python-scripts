#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a command to upgrade all installed pip packages. Run with python -m.

Usage:
    louie.piptools.upgrade_all [--quiet | --verbose] [options]
    louie.piptools.upgrade_all --help
    louie.piptools.upgrade_all --version

Options:
    --help       Print this help message and exit.
    --version    Print the current version of the script.

Output options:
    -v, --verbose    Print verbose output (useful for debugging.)
    -q, --quiet      Suppress the output of subprocess calls, i.e. quiet mode.
                     Note: This is currently unused; either the output command string
                     or '--run' will always output to stdout.

Script options:
    -r, --run        Run the resulting command instead of printing it. (DANGEROUS)
    --outdated       List only the outdated packages by adding '--outdated' to 'pip list'.
    --skip-checks    Skip checking the output of the 'pip list' command and parse it directly.

Python launcher options:
    --prefix <command>           The prefix to add before each 'pip' command. Overrides the py launcher
                                 when using Windows. Default is to base it off of '--python-version'.
                                 (Example: 'python3.8 -m')
    --python-version <version>   The version of Python to use when calling 'pip'. [default: 3]

"""

__version__ = "0.1.0"  # First working release

import re
import shlex
import string
import subprocess
import sys

from collections import deque
from typing import Iterable, List

from docopt import docopt

__all__ = ["get_packages", "generate_upgrade_command"]

PY_LAUNCHER_COMMAND = ["py", "<python-version>", "-m"]
PYTHON_COMMAND = ["python"]
PIP_LIST_COMMAND = ["pip", "list"]
PIP_UPGRADE_COMMAND = ["pip", "install", "--upgrade", "--no-cache-dir"]
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
    # Parse output into a list of lines and decode into str; strip
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


# ----- INTERACTIVE CODE ----
def main(args: List[str] = None):
    global rprint, vprint
    # Use duplicate imports, just to be safe :>
    import sys  # noqa

    if not args:
        args = docopt(__doc__, version=f"louie.piptools.upgrade_all: {__version__}")
    else:
        args = docopt(
            __doc__, argv=args, version=f"louie.piptools.upgrade_all: {__version__}"
        )

    # Enable verbose printing if necessary
    if args["--verbose"]:

        def vprint(text, *args, **kwargs):
            print(f"[DEBUG] {text}")

    # Disable all printing if necessary
    elif args["--quiet"]:
        rprint = vprint = lambda *args, **kwargs: None

    # Print processed arguments
    vprint(args)

    # Define base commands
    pip_list_command = deque(PIP_LIST_COMMAND)
    pip_upgrade_command = deque(PIP_UPGRADE_COMMAND)

    # ---> ARGUMENT PARSING
    # Check if we should use py launcher (only on Windows)
    use_py_launcher = sys.platform.startswith("win32")
    # Get python-version
    python_version = args["--python-version"].strip()
    # Append prefixes / py launcher if necessary
    if args["--prefix"]:
        prefix = shlex.split(args.prefix)
    elif use_py_launcher:
        prefix = PY_LAUNCHER_COMMAND.copy()
        prefix[prefix.index("<python-version>")] = f"-{python_version}"
    else:
        # Use 'python' on Windows, and 'python3.6' or the like on Unix-based systems
        if sys.platform.startswith("win32"):
            prefix = ["python", "-m"]
        else:
            prefix = [f"python{python_version}", "-m"]
    # Add prefix to all commands
    pip_list_command.extendleft(reversed(prefix))
    pip_upgrade_command.extendleft(reversed(prefix))

    # Add --outdated flag to pip_list_command if necessary
    if args["--outdated"]:
        pip_list_command.append("--outdated")

    # Debug print the commands
    vprint(f"pip_list_command: {pip_list_command}")
    vprint(f"pip_upgrade_command: {pip_upgrade_command}")

    # Main code
    packages = get_packages(list_command=pip_list_command)
    packages = list(packages)
    if not packages:
        if args["--outdated"]:
            rprint("All packages are up to date. Exiting normally.")
        else:
            vprint(
                "'pip list' returned an empty output and the --outdated flag was not specified."
            )
            vprint("Exiting normally.")
        raise SystemExit
    # Run if needed
    if args["--run"]:
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
