#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

from typing import List
from urllib.parse import unquote

URL_REGEX = re.compile("url=([^&]*)")


def get_url(google_url: str, regex=URL_REGEX):
    url = regex.search(google_url)
    if url is not None:
        return unquote(url[1])


def main(args: List[str] = None):
    import sys

    if args is None:
        args = sys.argv[1:]

    # Remove options from args, we currently do not have any
    args = [x for x in args if not x.startswith("-")]

    if len(args) < 1:
        urls = [input("Input URL here: ")]
    else:
        urls = args

    for i, url in enumerate(urls):
        i += 1  # Start counting at 1
        output = get_url(url)
        if output is not None:
            print(f"[{i}] {output}")
        else:
            print(f"[{i}] No URL found.")


if __name__ == "__main__":
    main()
