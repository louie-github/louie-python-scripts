#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json

from typing import TextIO, Union


class JSONArgumentParser(argparse.ArgumentParser):
    def __init__(self, json_file: Union[str, TextIO], *args, **kwargs):
        # Case 1: json_data is a file object
        json_data = self._load_json(json_file)
        self._parse_parser(json_data["parser"])
        self._parse_arguments(json_data["arguments"])

    @staticmethod
    def _load_json(json_file: Union[str, bytes, bytearray, TextIO]):
        try:
            return json.load(json_file)
        except AttributeError:
            # Case 2: json_data is a filename
            try:
                with open(json_file) as f:
                    return json.load(f)
            except FileNotFoundError:
                # Case 3: json_data is str with JSON data
                try:
                    return json.loads(json_file)
                except json.JSONDecodeError:
                    raise ValueError(
                        "Expected a filename, file-like object, or str with JSON data for argument 'json_file'"
                    )

    def _parse_parser(self, data: dict):
        return super().__init__(**data)

    def _parse_arguments(self, data: dict):
        for name, kwargs in data.items():
            # Processing steps:
            # 1. Replace the str 'argparse.REMAINDER' with the actual argparse.REMAINDER
            if kwargs.get("nargs") == "argparse.REMAINDER":
                kwargs["nargs"] = argparse.REMAINDER
            # 2. Get the additional aliases of the option
            names = [name]
            names.extend(kwargs.get("aliases", []))

            # FINAL: Call add_argument  with the option name(s) as positional
            # arguments and all other arguments as keyword arguments
            self.add_argument(*names, **kwargs)
