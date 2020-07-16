#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import shlex
import subprocess
import sys

__all__ = ["get_packages", "generate_upgrade_command"]

# Support for Python <3.8
try:
    shlex.join(["ignore", "this", "command"])
except AttributeError:

    def _shlex_join(split_command):
        """Return a shell-escaped string from *split_command*."""
        return " ".join(quote(arg) for arg in split_command)

    shlex.join = _shlex_join

PY_LAUNCHER_COMMAND = ["py", "-3.8", "-m"]
PIP_LIST_COMMAND = ["pip", "list"]
PIP_UPGRADE_COMMAND = ["pip", "install", "--upgrade", "--no-cache-dir"]
PIP_LIST_REGEX = re.compile(r"([\S]*) *(.*)")


def get_packages(list_command=PIP_LIST_COMMAND, regex=PIP_LIST_REGEX):
    sys_encoding = sys.stdout.encoding
    output = subprocess.check_output(list_command)
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


def generate_upgrade_command(
    packages=None,
    upgrade_command=PIP_UPGRADE_COMMAND,
    join_output=False,
    *args,
    **kwargs,
):
    # Get packages if not specified
    packages = packages if packages is not None else get_packages(*args, **kwargs)
    output = upgrade_command + packages
    if join_output:
        return shlex.join(output)
    else:
        return output


# ----- INTERACTIVE CODE -----
def main(args=None):
    # Use duplicate imports, just to be safe :>
    import argparse, sys  # noqa

    if not args:
        # Main arguments
        parser = argparse.ArgumentParser(
            description="Generate a command to update all installed pip packages"
        )
        parser.add_argument(
            "--run",
            help="Run the command rather than print it. DANGEROUS.",
            action="store_true",
            dest="run",
        )
        parser.add_argument(
            "--prefix",
            help=(
                "If specified, the prefix to use before all pip <command> strings. "
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
        pip_list_command = PY_LAUNCHER_COMMAND + pip_list_command
        pip_upgrade_command = PY_LAUNCHER_COMMAND + pip_upgrade_command
    elif args.prefix:
        prefix = shlex.split(args.prefix)
        pip_list_command = prefix + pip_list_command
        pip_upgrade_command = prefix + pip_upgrade_command
    # Main code
    packages = get_packages(list_command=pip_list_command)
    # Run if needed
    if args.run:
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
