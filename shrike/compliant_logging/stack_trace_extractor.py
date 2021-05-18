# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import glob
import os
import re
from typing import List
from shrike.compliant_logging.exceptions import (
    PublicValueError,
    print_prefixed_stack_trace_and_raise,
)


class StackTraceExtractor:
    """
    A class to perform extraction of stack traces, exception types and
    optionally exception messages from files that might contain other
    sensitive data.

    Attributes
    ----------
    show_exception_message : bool
        True to extract exception messages. False to skip them.
    prefix : bool
        Prefix to prepend extracted lines with. Defaults to "SystemLog".

    Methods
    -------
    extract(path):
        Extracts traces and exceptions from file to stdout.
    """

    def __init__(
        self,
        show_exception_message: bool = False,
        prefix: str = "SystemLog",
    ):
        self.in_python_traceback = False
        self.show_exception_message = show_exception_message
        self.prefix = prefix

    def _parse_trace_python(self, string: str):
        r = re.compile(r"Traceback \(most recent call last\):")
        m = r.search(string)
        if m:
            self.in_python_traceback = True
            return None

        r = re.compile(r"File (?P<file>.*), line (?P<line>\d*), in (?P<method>.*)")
        m = r.search(string)
        if m:
            return m

        r = re.compile(r"(?P<type>.*Error): (?P<message>.*)")
        m = r.search(string)
        if m and self.in_python_traceback:
            self.in_python_traceback = False
            return m

        return None

    @staticmethod
    def _parse_trace_csharp(string: str):
        r = re.compile(
            r"at (?P<namespace>.*)\.(?P<class>.*)\.(?P<method>.*) in (?P<file>.*):line (?P<line>\d*)"  # noqa:501
        )
        m = r.search(string)
        if m:
            return m

        r = re.compile(r"Unhandled exception. (?P<type>.*): (?P<message>.*)")
        m = r.search(string)
        if m:
            return m

        return None

    def _parse_file(self, file: str) -> None:
        print(f"{self.prefix}: Parsing file {os.path.abspath(file)}")
        with open(file, "r") as f:
            for line in f:
                m = StackTraceExtractor._parse_trace_csharp(line)
                if m and m.groupdict().get("type"):
                    print(f"{self.prefix}: type: {m.groupdict()['type']}")
                    if self.show_exception_message:
                        print(f"{self.prefix}: message: {m.groupdict()['message']}")
                    continue

                elif m and m.groupdict().get("namespace"):
                    print(f"{self.prefix}: namespace: {m.groupdict()['namespace']}")
                    print(f"{self.prefix}: class: {m.groupdict()['class']}")
                    print(f"{self.prefix}: method: {m.groupdict()['method']}")
                    print(f"{self.prefix}: file: {m.groupdict()['file']}")
                    print(f"{self.prefix}: line: {m.groupdict()['line']}")
                    print()
                    continue

                m = self._parse_trace_python(line)
                if m and m.groupdict().get("type"):
                    print(f"{self.prefix}: type: {m.groupdict()['type']}")
                    if self.show_exception_message:
                        print(f"{self.prefix}: message: {m.groupdict()['message']}")
                        print()
                elif m and m.groupdict().get("file"):
                    print(f"{self.prefix}: file: {m.groupdict()['file']}")
                    print(f"{self.prefix}: line: {m.groupdict()['line']}")
                    print(f"{self.prefix}: method: {m.groupdict()['method']}")

    def _get_files(self, path) -> List[str]:
        if os.path.isfile(path):
            print(f"{self.prefix}: Input is a file")
            return [path]
        if os.path.isdir(path):
            print(f"{self.prefix}: Input is a directory")
            files = glob.glob(path + "/*.err")
            return files
        else:
            raise PublicValueError("Provided path is neither a file nor a directory")

    def extract(self, path: str) -> None:
        """
        Run extraction on the given resources. Extracted traces and exceptions
        will be printed to stdout.
        Args:
            path (str): file or path. If path, extraction will be performed on
            all files with '.err' extension within that directory (not recursive).
            Hidden files will be ignored.
        """
        try:
            for file in self._get_files(path):
                self._parse_file(file)
            assert False
        except BaseException as e:
            print(f"{self.prefix}: There is a problem with the exceptionExtractor.")
            print_prefixed_stack_trace_and_raise(err=e, keep_message=True)
