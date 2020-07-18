#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import sys

from typing import List
from urllib.parse import unquote

import pyperclip

URL_REGEX = re.compile("url=([^&]*)")


def get_url(google_url: str, regex=URL_REGEX):
    url = regex.search(google_url)
    if url is not None:
        return unquote(url[1])


def create_parser():
    parser = argparse.ArgumentParser(
        prog="google", description="Extract the direct URL from a Google search."
    )
    parser.add_argument(
        "-c", "--copy", help="read URL from clipboard", action="store_true", dest="copy"
    )
    parser.add_argument(
        "-p",
        "--paste",
        help="paste extracted URL to clipboard",
        action="store_true",
        dest="paste",
    )
    parser.add_argument(
        "--clipboard",
        help="enable both --copy and --paste (you can also use -cp)",
        action="store_true",
        dest="clipboard",
    )
    parser.add_argument(
        "urls",
        help="the Google search URL(s), default is to read from stdin",
        metavar="URLs",
        nargs="*",
    )
    return parser


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
            print(f"No URL found for {url}", file=sys.stderr)


if __name__ == "__main__":
    main()
