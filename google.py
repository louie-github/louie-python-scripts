#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from urllib.parse import unquote

URL_REGEX = re.compile("url=([^&]*)")


def get_url(google_url: str, regex=URL_REGEX):
    url = regex.search(google_url)[1]
    if url is not None:
        return unquote(url)


def main():
    import sys

    if len(sys.argv) < 2:
        urls = [input("Input URL here: ")]
    else:
        urls = sys.argv[1:]
    for url in urls:
        print(get_url(url))


if __name__ == "__main__":
    main()
