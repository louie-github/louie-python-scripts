#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json

from typing import TextIO, Union


class JSONArgumentParser(argparse.ArgumentParser):
    def __init__(self, json_file: Union[str, TextIO], *args, **kwargs):
        json_data = self._load_json(json_file)
        self.json_data = json_data

        # Copy JSON data to preserve the original
        json_data = json_data.copy()

        if parser_data := json_data.get("parser"):
            self._parse_parser(parser_data)

        if arguments_data := json_data.get("arguments"):
            self._parse_arguments(arguments_data)

        if groups_data := json_data.get("groups"):
            self._parse_groups(groups_data)

        self._json_data_after_parsing = json_data

    @staticmethod
    def _load_json(json_file: Union[str, bytes, bytearray, TextIO]):
        # Case 1: json_data is a file object
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

    @staticmethod
    def _process_argument(name, kwargs):
        # Processing steps:
        # 1. Replace the str 'argparse.REMAINDER' with the actual argparse.REMAINDER
        if kwargs.get("nargs") == "argparse.REMAINDER":
            kwargs["nargs"] = argparse.REMAINDER
        # 2. Get the additional aliases of the option
        names = [name]
        names.extend(kwargs.pop("aliases", []))

        return names, kwargs

    def _parse_arguments(self, data: dict):
        # Cache the dictionary lookup
        _process_argument = self._process_argument

        for name, kwargs in data.items():
            names, kwargs = _process_argument(name, kwargs)
            self.add_argument(*names, **kwargs)

    def _parse_groups(self, data: dict):
        # Cache the dictionary lookup
        _process_argument = self._process_argument

        for group_name, group_kwargs in data.items():
            # Remove 'arguments' and 'mutually_exclusive' so we don't
            # accidentally pass them as keyword arguments
            arguments = group_kwargs.pop("arguments", None)
            mutually_exclusive = group_kwargs.pop("mutually_exclusive", False)

            # Create the group
            if mutually_exclusive:
                group = self.add_mutually_exclusive_group(**group_kwargs)
            else:
                group = self.add_argument_group(**group_kwargs)

            # Add arguments to group
            if arguments is not None:
                for name, kwargs in arguments.items():
                    names, kwargs = _process_argument(name, kwargs)
                    group.add_argument(*names, **kwargs)
