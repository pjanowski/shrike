# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import io
import pickle
import pytest
import re
import sys
from traceback import TracebackException
import uuid


from shrike.confidential_logging.exceptions import (
    _PrefixStackTraceWrapper,
    prefix_stack_trace,
    SCRUB_MESSAGE,
    PREFIX,
    is_exception_allowed,
    PrefixStackTrace,
    PublicArgumentError,
    PublicRuntimeError,
    PublicValueError,
    PublicKeyError,
    PublicTypeError,
    PublicIndexError,
    PublicNotImplementedError,
    PublicFileNotFoundError,
    PublicIOError,
    print_prefixed_stack_trace_and_raise,
    scrub_exception,
)


@pytest.mark.parametrize(
    "message,exec_type",
    [("foo", ArithmeticError), ("secret data", KeyError), ("baz", Exception)],
)
def test_prefix_stack_trace_preserves_exception_type(message: str, exec_type):
    """
    Verify that the exception type and "scrub message" appear in the
    prefixed lines.
    """
    file = io.StringIO()

    @prefix_stack_trace(file)
    def function():
        raise exec_type(message)

    with pytest.raises(exec_type):
        function()

    log_lines = file.getvalue()
    assert exec_type.__name__ in log_lines
    assert SCRUB_MESSAGE in log_lines


def test_prefix_stack_trace_works_with_sys_exit():
    file = io.StringIO()

    @prefix_stack_trace(file, allow_list=["SystemExit"])
    def function():
        sys.exit(1)

    with pytest.raises(SystemExit) as e:
        function()

    assert e.value.args[0] == 1

    log_lines = file.getvalue()
    assert "SystemExit: 1" in log_lines


def test_prefix_stack_trace_works_with_file_not_found():
    file = io.StringIO()
    file_name = str(uuid.uuid4())

    @prefix_stack_trace(file, allow_list=["FileNotFoundError"])
    def function():
        with open(file_name) as f:
            str(f)

    with pytest.raises(FileNotFoundError):
        function()

    log_lines = file.getvalue()
    assert f"SystemLog:No such file or directory: 'SystemLog:{file_name}'" in log_lines


def test_prefix_stack_trace_replaces_exception_with_readonly_attribute():
    class UnmodifiableError(Exception):
        def __init__(self):
            super().__init__()

        @property
        def unmodifiable(self):
            return "you can't change me"

    file = io.StringIO()

    @prefix_stack_trace(file)
    def function():
        raise UnmodifiableError()

    with pytest.raises(PublicRuntimeError):
        function()

    log_lines = file.getvalue()
    assert (
        "SystemLog: Obtained AttributeError when trying to scrub unmodifiable from UnmodifiableError"  # noqa: E501
        in log_lines
    )


def test_prefix_stack_trace_succeeds_when_no_message():
    """
    Verify that exceptions without message are re-raised correctly.
    """
    file = io.StringIO()

    @prefix_stack_trace(file, keep_message=True)
    def function():
        assert False

    with pytest.raises(AssertionError):
        function()

    log_lines = file.getvalue()
    assert AssertionError.__name__ in log_lines


def test_prefix_stack_trace_respects_disable():
    """
    Verify that the parameter `disable` of `prefix_stack_trace` turns off the
    functionality that decorator implements.
    """
    file = io.StringIO()

    @prefix_stack_trace(file, disable=True)
    def function():
        raise Exception()

    with pytest.raises(Exception):
        function()

    assert file.getvalue() == ""


@pytest.mark.parametrize(
    "prefix,exec_type,message,keep",
    [
        ("foo", ArithmeticError, "secret data", False),
        ("baz", Exception, "you shouldn't see this", True),
    ],
)
def test_prefix_stack_trace_respects_keep_message(prefix, exec_type, message, keep):
    with pytest.raises(exec_type) as exec_info:
        with PrefixStackTrace(prefix=prefix, keep_message=keep):
            raise exec_type(message)

    assert prefix in str(exec_info.value)
    assert (message in str(exec_info.value)) == keep


def test_prefix_stack_trace_default_doesnt_keep_message():
    with pytest.raises(Exception) as exec_info:
        with PrefixStackTrace(prefix="pref"):
            raise Exception("msg")

    assert "msg" not in str(exec_info.value)


@pytest.mark.parametrize("prefix", ["foo__"])
def test_prefix_stack_trace_respects_prefix(prefix):
    """
    Verify that the prefix added in by `prefix_stack_trace` respects the
    provided configuration.
    """
    file = io.StringIO()

    @prefix_stack_trace(file, prefix=prefix)
    def function():
        raise Exception()

    with pytest.raises(Exception):
        function()

    assert prefix in file.getvalue()


@pytest.mark.parametrize(
    "disable,prefix,message", [(False, "pref", "mess"), (True, "foo", "bar")]
)
def test_prefix_stack_trace_respects_scrub_message(disable, prefix, message):
    """
    Verify that the "message scrubbed" string added in by `prefix_stack_trace`
    respects the provided configuration.
    """
    file = io.StringIO()

    def function():
        raise Exception(message)

    with pytest.raises(Exception):
        with PrefixStackTrace(
            disable=disable, prefix=prefix, scrub_message=message, file=file
        ):
            function()

    file_value = file.getvalue()
    if disable:
        assert "" == file_value
    else:
        assert prefix in file_value
        assert message in file_value


@pytest.mark.parametrize(
    "keep_message, allow_list, expected_result",
    [
        (
            False,
            ["arithmetic", "ModuleNotFound"],
            True,
        ),  # scrub_message with allow_list
        (False, [], False),  # scrub_message
        (True, [], True),
    ],
)  # keep_message
def test_prefix_stack_trace_nested_exception(keep_message, allow_list, expected_result):
    file = io.StringIO()

    def function1():
        import my_custom_library

        my_custom_library.foo()

    @prefix_stack_trace(file, keep_message=keep_message, allow_list=allow_list)
    def function2():
        try:
            function1()
        except ModuleNotFoundError:
            raise ArithmeticError()

    with pytest.raises(ArithmeticError):
        function2()

    assert ("No module named" in file.getvalue()) == expected_result


@pytest.mark.parametrize(
    "allow_list, expected_result",
    [
        (["ModuleNotFound"], True),  # allow_list match error type
        (["arithmetic", "ModuleNotFound"], True),  # allow_list multiple strings
        (["geometry", "algebra"], False),  # allow_list no match
        (["my_custom_library"], True),  # allow_list match error message
    ],
)
def test_prefix_stack_trace_allow_list(allow_list, expected_result):
    file = io.StringIO()
    message = "No module named"

    @prefix_stack_trace(file, allow_list=allow_list)
    def function():
        import my_custom_library

        my_custom_library.foo()

    with pytest.raises(Exception):
        function()

    assert (message in file.getvalue()) == expected_result


@pytest.mark.parametrize(
    "allow_list, expected_result",
    [
        (["argparse", "ModuleNotFound"], True),
        (["argparse", "type"], False),
        (["Bingo..+Pickle"], True),
        ([], False),
    ],
)
def test_is_exception_allowed(allow_list, expected_result):
    exception = ModuleNotFoundError("Bingo. It is a pickle.")
    res = is_exception_allowed(TracebackException.from_exception(exception), allow_list)
    assert res == expected_result


@pytest.mark.parametrize(
    "keep_message, allow_list",
    [
        (True, []),  # unscrub message
        (False, []),  # scrub message
        (False, ["ValueError"]),  # unscrub whitelisted message
    ],
)
def test_prefix_stack_trace_throws_correctly(keep_message, allow_list):
    """
    After logging the library continues execution by rethrowing an error. The final
    error thrown is picked up for error reporting by AML. It should be consistent
    with user's scrubbing choice. Verify that the scrubber preserves the exception type
    and correctly modifies the exception message
    """
    file = io.StringIO()

    message = "This is the original exception message"
    e_type = ValueError

    @prefix_stack_trace(file, keep_message=keep_message, allow_list=allow_list)
    def function():
        raise e_type(message)

    with pytest.raises(e_type) as info:
        function()

    if keep_message is True or is_exception_allowed(
        TracebackException.from_exception(info.value), allow_list
    ):
        assert message in str(info.value)
    else:
        assert SCRUB_MESSAGE in str(info.value)

    assert PREFIX in str(info.value)
    assert info.type == e_type


@pytest.mark.parametrize(
    "allow_list,disable,file,keep_message,prefix,scrub_message, add_timestamp",
    [([], True, io.StringIO(), "keep", "prefix", "scrub", True)],
)
def test__PrefixStackTraceWrapper_is_pickleable(
    allow_list, disable, file, keep_message, prefix, scrub_message, add_timestamp
):
    pst = _PrefixStackTraceWrapper(
        file, disable, prefix, scrub_message, keep_message, allow_list, add_timestamp
    )

    data = pickle.dumps(pst)
    unpickled = pickle.loads(data)

    assert isinstance(unpickled, _PrefixStackTraceWrapper)


@pytest.mark.parametrize("add_timestamp", [(False), (True)])
def test_prefix_stack_trace_respects_add_timestamp(add_timestamp):
    """
    Verify that scrubbed stack trace includes timestamp when
    add_timestamp parameter is set to true.
    """
    file = io.StringIO()

    def function():
        raise Exception("some exception message")

    with pytest.raises(Exception):
        with PrefixStackTrace(add_timestamp=add_timestamp, file=file):
            function()

    file_value = file.getvalue()
    timestamp_regex = r" [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} "
    timestamp_match = re.search(timestamp_regex, file_value.split("\n")[0])
    assert bool(timestamp_match) == add_timestamp
    print("hello")


@pytest.mark.parametrize(
    "exc_type,msg",
    [
        (PublicRuntimeError, "message"),
        (PublicValueError, "message"),
        (PublicKeyError, "message"),
        (PublicTypeError, "message"),
        (PublicIndexError, "a"),
        (PublicNotImplementedError, "b"),
        (PublicFileNotFoundError, "c"),
        (PublicIOError, "d"),
    ],
)
def test_public_exception_messages_are_preserved(exc_type, msg):
    file = io.StringIO()

    with pytest.raises(exc_type):
        with PrefixStackTrace(file=file):
            raise exc_type(msg)

    file_value = file.getvalue()

    assert re.search(fr"SystemLog\:.*{msg}", file_value)


def test_public_argument_error_message_is_preserved():
    file = io.StringIO()

    with pytest.raises(PublicArgumentError):
        with PrefixStackTrace(file=file):
            raise PublicArgumentError(None, "message")

    file_value = file.getvalue()

    assert re.search(r"SystemLog\:.*message", file_value)


@pytest.mark.parametrize("message,exc_type", [("hi", ArithmeticError)])
def test_default_allow_list_respected(message, exc_type):
    from shrike.confidential_logging.exceptions import default_allow_list

    default_allow_list.clear()
    default_allow_list.append(message)

    file = io.StringIO()

    @prefix_stack_trace(file)
    def function():
        raise exc_type(message)

    with pytest.raises(exc_type):
        function()

    file_value = file.getvalue()

    assert PREFIX in file_value
    assert message in file_value


def test_print_prefixed_stack_trace_and_raise_works_with_null_exception():
    file = io.StringIO()

    with pytest.raises(Exception):
        try:
            raise Exception("boo")
        except BaseException:
            print_prefixed_stack_trace_and_raise(file)

    assert PREFIX in file.getvalue()


def test_scrub_exception_works_with_loop_in_traceback():
    """
    This test will fail if `scrub_exception` doesn't use `_seen`.
    """
    try:
        try:
            raise Exception("boo")
        except Exception as e:
            raise e from e
    except BaseException as be:
        scrubbed = scrub_exception(be, SCRUB_MESSAGE, PREFIX, True, [])

    assert scrubbed is not None
