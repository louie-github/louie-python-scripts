#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import inspect
import json

from typing import TextIO, Union


def parse_json(json_data: Union[str, bytes, bytearray, TextIO]):
    # Try loading as file first, then as str
    try:
        json.load(json_data)
    except AttributeError:
        try:
            json.loads(json_data)
        except json.JSONDecodeError:
            raise ValueError("Expected a JSON file object or valid JSON data")


def _parse_arguments(data: dict):
    for name, kwargs in data.iteritems():
        # Processing steps:
        # 1. Replace the str 'argparse.REMAINDER' with the actual argparse.REMAINDER
        if kwargs.get("nargs") == "argparse.REMAINDER":
            kwargs["nargs"] = argparse.REMAINDER

        yield name, kwargs


def make_argparse(json_data: dict):
    # First, get all the non-arguments
    json_data = json_data.copy()
    argparse_args = inspect.getfullargspec(argparse.ArgumentParser)
    arguments = []
    for key in json_data.keys():
        if key == "arguments":
            arguments = _parse_arguments(json_data[key])


class JSONArgumentParser(argparse.ArgumentParser):
    def __init__(self, json_file, *args, **kwargs):
        json_data = parse_json(json_file)

