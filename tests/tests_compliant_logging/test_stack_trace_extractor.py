# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import shrike.compliant_logging.stack_trace_extractor as ste
import pathlib
import re


def test_parse_trace_csharp_parses_correctly():
    """
    Verify that csharp stack traces are parsed correctly.
    """
    extractor = ste.StackTraceExtractor()

    line = (
        r"at ExtractExceptions.ExceptionExtractor.Main(String[] args "
        r"in C:\code\ExP_Code\dotnetcore\errorParser\Program.cs:line 121"
    )
    match = extractor._parse_trace_csharp(line)
    assert len(match.groupdict()) == 5

    line = (
        "Unhandled exception. System.IndexOutOfRangeException: "
        "Index was outside the bounds of the array."
    )
    match = extractor._parse_trace_csharp(line)
    assert len(match.groupdict()) == 2

    line = "hello world"
    match = extractor._parse_trace_csharp(line)
    assert not match


def test_parse_trace_python_parses_correctly():
    """
    Verify that python stack traces are parsed correctly.
    """
    extractor = ste.StackTraceExtractor()

    line = r"Traceback (most recent call last):"
    match = extractor._parse_trace_python(line)
    assert not match
    assert extractor.in_python_traceback

    line = (
        r"File \"/mnt/c/code/shrike/shrike/compliant_logging/"
        r"exceptionExtractor.py\", line 28, in <module>"
    )
    match = extractor._parse_trace_python(line)
    assert len(match.groupdict()) == 3
    assert extractor.in_python_traceback

    line = r"print(10/0)"
    match = extractor._parse_trace_python(line)
    assert not match
    assert extractor.in_python_traceback

    line = "ZeroDivisionError: division by zero"
    match = extractor._parse_trace_python(line)
    assert len(match.groupdict()) == 2
    assert not extractor.in_python_traceback

    line = "hello world"
    match = extractor._parse_trace_python(line)
    assert not match
    assert not extractor.in_python_traceback


def test_parse_file(capsys):
    """
    Verify that parsing entire file runs correctly.
    """

    HERE = pathlib.Path(__file__).parent
    file = str(HERE / "log.err")
    extractor = ste.StackTraceExtractor()
    extractor._parse_file(file)
    captured = capsys.readouterr()
    target = (
        r"^SystemLog: Parsing file .+\n"
        r"SystemLog: type: System.IndexOutOfRangeException\n"
        r"SystemLog: namespace: ExtractExceptions\n"
        r"SystemLog: class: ExceptionExtractor\n"
        r"SystemLog: method: .+\n"
        r"SystemLog: file: .+\n"
        r"SystemLog: line: 121\n\n"
        r"SystemLog: file: .+\n"
        r"SystemLog: line: 28\n"
        r"SystemLog: method: <module>\n"
        r"SystemLog: type: ZeroDivisionError\n$"
    )

    assert re.match(target, captured.out)
    assert len(captured.out.split("\n")) == 13
