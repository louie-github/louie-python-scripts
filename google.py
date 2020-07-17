#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

from typing import List
from urllib.parse import unquote

URL_REGEX = re.compile("url=([^&]*)")


def get_url(google_url: str, regex=URL_REGEX):
    url = regex.search(google_url)[1]
    if url is not None:
        return unquote(url)


def main(args: List[str] = None):
    import sys

    if args is None:
        args = sys.argv[1:]

    if len(args) < 1:
        urls = [input("Input URL here: ")]
    else:
        urls = args

    for url in urls:
        print(get_url(url))


if __name__ == "__main__":
    main()
