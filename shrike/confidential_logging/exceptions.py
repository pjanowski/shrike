# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Decorators and utilities for prefixing exception stack traces while obscuring
the exception message itself.
"""


import argparse
from collections.abc import Iterable
import functools
import re
import sys
import time
from traceback import TracebackException

# https://stackoverflow.com/a/38569536
from typing import Callable, Optional, Set, TextIO, Union


PREFIX = "SystemLog:"
SCRUB_MESSAGE = "**Exception message scrubbed**"


class PublicValueError(ValueError):
    """
    Value error with public message. Exceptions of this type raised under
    `prefix_stack_trace` or `print_prefixed_stack_trace_and_raise` will have
    the message prefixed with `PREFIX` in both the printed stack trace and the
    re-raised exception.
    """


class PublicRuntimeError(RuntimeError):
    """
    Runtime error with public message. Exceptions of this type raised under
    `prefix_stack_trace` or `print_prefixed_stack_trace_and_raise` will have
    the message prefixed with `PREFIX` in both the printed stack trace and the
    re-raised exception.
    """


class PublicArgumentError(argparse.ArgumentError):
    """
    Argument error with public message. Exceptions of this type raised under
    `prefix_stack_trace` or `print_prefixed_stack_trace_and_raise` will have
    the message prefixed with `PREFIX` in both the printed stack trace and the
    re-raised exception.
    """


class PublicKeyError(KeyError):
    """
    Key error with public message. Exceptions of this type raised under
    `prefix_stack_trace` or `print_prefixed_stack_trace_and_raise` will have
    the message prefixed with `PREFIX` in both the printed stack trace and the
    re-raised exception.
    """


class PublicTypeError(TypeError):
    """
    Type error with public message. Exceptions of this type raised under
    `prefix_stack_trace` or `print_prefixed_stack_trace_and_raise` will have
    the message prefixed with `PREFIX` in both the printed stack trace and the
    re-raised exception.
    """


class PublicIndexError(IndexError):
    """
    Index error with public message. Exceptions of this type raised under
    `prefix_stack_trace` or `print_prefixed_stack_trace_and_raise` will have
    the message prefixed with `PREFIX` in both the printed stack trace and the
    re-raised exception.
    """


class PublicNotImplementedError(NotImplementedError):
    """
    Not implemented error with public message. Exceptions of this type raised
    under `prefix_stack_trace` or `print_prefixed_stack_trace_and_raise` will
    have the message prefixed with `PREFIX` in both the printed stack trace and
    the re-raised exception.
    """


class PublicFileNotFoundError(FileNotFoundError):
    """
    File not found error with public message. Exceptions of this type raised
    under `prefix_stack_trace` or `print_prefixed_stack_trace_and_raise` will
    have the message prefixed with `PREFIX` in both the printed stack trace and
    the re-raised exception.
    """


class PublicIOError(IOError):
    """
        I/O error with public message. Exceptions of this type raised
    under `prefix_stack_trace` or `print_prefixed_stack_trace_and_raise` will
        have the message prefixed with `PREFIX` in both the printed stack trace and
        the re-raised exception.
    """


default_allow_list = [
    PublicValueError.__name__,
    PublicRuntimeError.__name__,
    PublicArgumentError.__name__,
    PublicKeyError.__name__,
    PublicTypeError.__name__,
    PublicIndexError.__name__,
    PublicNotImplementedError.__name__,
    PublicFileNotFoundError.__name__,
    PublicIOError.__name__,
]


def _attribute_transformer(prefix: str, scrub_message: str, keep: bool) -> Callable:
    """
    Create a function which may be used to transform exception attributes.

    If an attribute is string-valued, apply the logic keep? prefix + attr: prefix
    + scrub_message.

    If the attribute is iterable, apply this logic to each member of the
    attribute.

    If the attribute is callable, don't change it.

    If it is neither, replace it with None to ensure no private data leaks.
    """

    def inner(o):
        rv = o
        if isinstance(o, str):
            if keep:
                rv = prefix + o
            else:
                rv = prefix + scrub_message
        elif isinstance(o, Iterable):
            rv = type(o)(map(inner, o))  # type: ignore
        elif callable(o):
            rv = rv
        elif not keep:
            rv = None

        return rv

    return inner


def scrub_exception(
    exception: Optional[BaseException],
    scrub_message: str,
    prefix: str,
    keep_message: bool,
    allow_list: list,
    _seen: Optional[Set[int]] = None,
) -> Optional[BaseException]:
    """
    Recursively scrub all potentially private data from an exception, using the
    logic in `_attribute_transformer`.

    Inspired by Dan Schwartz's closed-source implementation:
    https://dev.azure.com/eemo/TEE/_git/TEEGit?path=%2FOffline%2FFocusedInbox%2FComTriage%2Fcomtriage%2Futils%2Fscrubber.py&version=GBcompliant%2FComTriage&_a=content

    which is closely based on the CPython implementation of the
    TracebackException class:
    https://github.com/python/cpython/blob/master/Lib/traceback.py#L478
    """
    if not exception:
        return None

    # Handle loops in __cause__ or __context__ .
    if _seen is None:
        _seen = set()
    _seen.add(id(exception))

    # Gracefully handle being called with no type or value.
    if exception.__cause__ is not None and id(exception.__cause__) not in _seen:
        exception.__cause__ = scrub_exception(
            exception.__cause__,
            scrub_message,
            prefix,
            keep_message,
            allow_list,
            _seen,
        )
    if exception.__context__ is not None and id(exception.__context__) not in _seen:
        exception.__context__ = scrub_exception(
            exception.__context__,
            scrub_message,
            prefix,
            keep_message,
            allow_list,
            _seen,
        )

    keep = keep_message or is_exception_allowed(exception, allow_list)
    transformer = _attribute_transformer(prefix, scrub_message, keep)

    for attr in dir(exception):
        if attr and not attr.startswith("__"):
            try:
                value = getattr(exception, attr)
            except AttributeError:
                # In some cases, e.g. FileNotFoundError, there are attributes
                # which show up in dir(e), but for which an AttributeError is
                # thrown when attempting to access the value. See, e.g.:
                # https://stackoverflow.com/q/47775772 .
                continue
            try:
                # If unable to transform or set the attribute, replace the
                # entire exception since the attribute value is readable, but
                # we are unable to scrub it.
                new_value = transformer(value)
                setattr(exception, attr, new_value)
            except BaseException as e:
                new_exception = PublicRuntimeError(
                    f"{prefix} Obtained {type(e).__name__} when trying to scrub {attr} from {type(exception).__name__}"  # noqa: E501
                )
                new_exception.__cause__ = exception.__cause__
                new_exception.__context__ = exception.__context__
                exception = new_exception
                break

    return exception


def is_exception_allowed(
    exception: Union[BaseException, TracebackException], allow_list: list
) -> bool:
    """
    Check if message is allowed, either by `allow_list`, or `default_allow_list`.

    Args:
        exception (TracebackException): the exception to test
        allow_list (list): list of regex expressions. If any expression matches
            the exception name or message, it will be considered allowed.

    Returns:
        bool: True if message is allowed, False otherwise.
    """
    if not isinstance(exception, TracebackException):
        exception = TracebackException.from_exception(exception)

    # empty list means all messages are allowed
    for expr in allow_list + default_allow_list:
        if re.search(expr, getattr(exception, "_str", ""), re.IGNORECASE):
            return True
        if re.search(expr, getattr(exception.exc_type, "__name__", ""), re.IGNORECASE):
            return True
    return False


def print_prefixed_stack_trace_and_raise(
    file: TextIO = sys.stderr,
    prefix: str = PREFIX,
    scrub_message: str = SCRUB_MESSAGE,
    keep_message: bool = False,
    allow_list: list = [],
    add_timestamp: bool = False,
    err: Optional[BaseException] = None,
) -> None:
    """
    Print the current exception and stack trace to `file` (usually client
    standard error), prefixing the stack trace with `prefix`.
    Args:
        keep_message (bool): if True, don't scrub message. If false, scrub (unless
            allowed).
        allow_list (list): exception allow_list. Ignored if keep_message is True. If
            empty all messages will be srubbed.
        err: the error that was thrown. None accepted for backwards compatibility.
    """
    if err is None:
        err = sys.exc_info()[1]
    scrubbed_err = scrub_exception(err, scrub_message, prefix, keep_message, allow_list)

    tb_exception = TracebackException.from_exception(scrubbed_err)  # type: ignore

    for execution in tb_exception.format():
        if "return function(*func_args, **func_kwargs)" in execution:
            # Do not show the stack trace for our decorator.
            continue
        for line in execution.splitlines():
            if add_timestamp:
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print(f"{prefix} {current_time} {line}", file=file)
            else:
                print(f"{prefix} {line}", file=file)

    raise scrubbed_err  # type: ignore


class _PrefixStackTraceWrapper:
    """
    Callable object for catching exceptions and printing their stack traces,
    appropriately prefixed.

    This is an object instead of a nested function to support working in Spark.
    Python anonymous functions are not "pickleable", so we need to define a
    class which handles this logic, so the class is picklable.
    """

    def __init__(
        self,
        file: TextIO,
        disable: bool,
        prefix: str,
        scrub_message: str,
        keep_message: bool,
        allow_list: list,
        add_timestamp: bool,
    ) -> None:
        self.allow_list = allow_list
        self.disable = disable
        self.file = file
        self.keep_message = keep_message
        self.prefix = prefix
        self.scrub_message = scrub_message
        self.add_timestamp = add_timestamp

    def __call__(self, function) -> Callable:
        @functools.wraps(function)
        def wrapper(*func_args, **func_kwargs):
            """
            Create a wrapper which catches exceptions thrown by `function`,
            scrub exception messages, and logs the prefixed stack trace.
            """
            caught_err = None
            try:
                return function(*func_args, **func_kwargs)
            except BaseException as err:
                caught_err = err

            if caught_err:
                print_prefixed_stack_trace_and_raise(
                    self.file,
                    self.prefix,
                    self.scrub_message,
                    self.keep_message,
                    self.allow_list,
                    self.add_timestamp,
                    caught_err,
                )

        return function if self.disable else wrapper


def prefix_stack_trace(
    file: TextIO = sys.stderr,
    disable: bool = bool(sys.flags.debug),
    prefix: str = PREFIX,
    scrub_message: str = SCRUB_MESSAGE,
    keep_message: bool = False,
    allow_list: list = [],
    add_timestamp: bool = False,
) -> Callable:
    """
    Decorator which wraps the decorated function and prints the stack trace of
    exceptions which occur, prefixed with `prefix` and with exception messages
    scrubbed (replaced with `scrub_message`). To use this, just add
    `@prefix_stack_trace()` above your function definition, e.g.

        @prefix_stack_trace()
        def foo(x):
            pass
    """

    return _PrefixStackTraceWrapper(
        file, disable, prefix, scrub_message, keep_message, allow_list, add_timestamp
    )


class PrefixStackTrace:
    def __init__(
        self,
        file: TextIO = sys.stderr,
        disable: bool = bool(sys.flags.debug),
        prefix: str = PREFIX,
        scrub_message: str = SCRUB_MESSAGE,
        keep_message: bool = False,
        add_timestamp: bool = False,
        allow_list: list = [],
    ):
        self.file = file
        self.disable = disable
        self.prefix = prefix
        self.scrub_message = scrub_message
        self.keep_message = keep_message
        self.add_timestamp = add_timestamp
        self.allow_list = allow_list

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type and not self.disable:
            print_prefixed_stack_trace_and_raise(
                file=self.file,
                prefix=self.prefix,
                scrub_message=self.scrub_message,
                keep_message=self.keep_message,
                allow_list=self.allow_list,
                add_timestamp=self.add_timestamp,
                err=exc_value,
            )
