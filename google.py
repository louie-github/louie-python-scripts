#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# Copyright 2020 louie-github
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import re
import sys

from functools import partial
from pathlib import Path
from typing import List
from urllib.parse import unquote


import pyperclip

from .core import JSONArgumentParser

CLI_JSON_CONFIG_FILE = Path(__file__).parent / "cli" / f"{Path(__file__).stem}.json"

URL_REGEX = re.compile("url=([^&]*)")


def get_url(google_url: str, regex=URL_REGEX):
    url = regex.search(google_url)
    if url is not None:
        return unquote(url[1])


def create_parser():
    return JSONArgumentParser(json_file=CLI_JSON_CONFIG_FILE)


def configure(args: argparse.Namespace):
    clipboard, copy, paste, urls, = (
        args.clipboard,
        args.copy,
        args.paste,
        args.urls,
    )
    printer = print

    # Use modular checks
    if clipboard:
        copy = True
        paste = True

    if copy:
        urls.extend([url.strip() for url in pyperclip.paste().splitlines()])

    if paste:
        printer = pyperclip.copy

    return urls, printer


def main(args: List[str] = None):
    _errprint = partial(print, file=sys.stderr)

    parser = create_parser()
    parsed_args = parser.parse_args(args)
    urls, printer = configure(parsed_args)

    # Use stdin if no URLs were given, like a good program :>
    if not urls:
        urls = (url.strip() for url in sys.stdin.read().splitlines())

    # Main loop
    for url in urls:
        output = get_url(url)
        if output:
            printer(output)
        else:
            _errprint(f"No URL found for {url}", file=sys.stderr)


if __name__ == "__main__":
    main()
