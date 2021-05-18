# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from shrike import compliant_logging
from shrike.compliant_logging.constants import DataCategory
import io
import logging
import pytest
import re
import sys


def test_basic_config():
    logging.warning("before basic config")

    logging.basicConfig()
    logging.warning("warning from test_basic_config")

    log = logging.getLogger("foo")
    log.warning("warning from foo logger")


class StreamHandlerContext:
    """
    Add, then remove a stream handler with the provided format string. The
    `__str__` method on this class returns the value of the internal stream.
    """

    def __init__(self, log, fmt: str):
        self.logger = log
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setLevel(log.getEffectiveLevel())
        self.handler.setFormatter(logging.Formatter(fmt))

    def __enter__(self):
        self.logger.addHandler(self.handler)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.logger.removeHandler(self.handler)
        self.handler.flush()

    def __str__(self):
        return self.stream.getvalue()


@pytest.mark.parametrize("level", ["debug", "info", "warning", "error", "critical"])
def test_data_category_and_log_info_works_as_expected(level):
    compliant_logging.enable_compliant_logging()

    log = logging.getLogger()
    log.setLevel(level.upper())

    assert isinstance(log, compliant_logging.logging.CompliantLogger)

    with StreamHandlerContext(
        log, "%(prefix)s%(levelname)s:%(name)s:%(message)s"
    ) as context:
        func = getattr(log, level)
        func("PRIVATE")
        func("public", category=DataCategory.PUBLIC)
        logs = str(context)

    assert re.search(r"^SystemLog\:.*public$", logs, flags=re.MULTILINE)
    assert not re.search(r"^SystemLog\:.*\:PRIVATE", logs, flags=re.MULTILINE)


def test_non_category_aware_logging_works_as_expected():
    compliant_logging.enable_compliant_logging()

    log = logging.getLogger()
    extra = {"test_name": "", "test_id": ""}
    assert isinstance(log, compliant_logging.logging.CompliantLogger)
    with StreamHandlerContext(
        log, "%(test_name)s:%(test_id)s %(prefix)s%(levelname)s:%(name)s:%(message)s"
    ) as context:
        log.log(1, "message", extra={"test_name": "Test", "test_id": 1})
        log.debug("message", extra={"test_name": "Test2", "test_id": 0})
        log.info("message", extra=extra)
        log.warning("message", extra={"test_name": "My", "test_id": "a"})
        try:
            1 / 0
        except Exception as e:
            logging.error(
                "Error at division",
                exc_info=e,
                stack_info=True,
                extra={"test_name": "Test", "test_id": 1},
            )
        log.critical("message", extra=extra, stack_info=True)
        logs = str(context)

    assert re.search(r"^Test:1 Level 1:root:message$", logs, flags=re.MULTILINE)
    assert re.search(r"^Test2:0 DEBUG:root:message$", logs, flags=re.MULTILINE)
    assert re.search(r"^: INFO:root:message$", logs, flags=re.MULTILINE)
    assert re.search(r"^My:a WARNING:root:message$", logs, flags=re.MULTILINE)
    assert re.search(
        r"^Test:1 ERROR:root:Error at division\nTraceback(.*\n){4}Stack",
        logs,
        flags=re.MULTILINE,
    )
    assert re.search(r"^: CRITICAL:root:message\nStack", logs, flags=re.MULTILINE)


@pytest.mark.parametrize("exec_type,message", [(ArithmeticError, "1+1 != 3")])
def test_exception_works_as_expected(exec_type, message):
    compliant_logging.enable_compliant_logging()
    log = logging.getLogger()
    assert isinstance(log, compliant_logging.logging.CompliantLogger)

    with StreamHandlerContext(
        log, "%(prefix)s%(levelname)s:%(name)s:%(message)s"
    ) as context:
        try:
            raise exec_type(message)
        except exec_type:
            log.error("foo", category=DataCategory.PUBLIC)
        logs = str(context)

    assert re.search(r"^SystemLog\:.*foo$", logs, flags=re.MULTILINE)


def test_all_the_stuff():
    compliant_logging.enable_compliant_logging()
    log = logging.getLogger("foo")
    log.info("public", category=DataCategory.PUBLIC)
    log.info("PRIVATE", category=DataCategory.PRIVATE)

    log.info("PRIVATE2")


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Requires Python >= 3.8")
def test_enable_compliant_logging_sets_force():
    # Pytest adds handlers to the root logger by default.
    initial_handlers = list(logging.root.handlers)

    compliant_logging.enable_compliant_logging()

    assert len(logging.root.handlers) == 1
    assert all(h not in logging.root.handlers for h in initial_handlers)


def test_warn_if_root_handlers_already_exist(capsys):
    # Pytest adds handlers to the root logger by default.

    compliant_logging.enable_compliant_logging()

    # https://docs.pytest.org/en/stable/capture.html
    stderr = capsys.readouterr().err
    assert "SystemLog:The root logger already has handlers set!" in stderr


def test_deprecated_enable_confidential_logging(capsys):
    """Pytest the pending deprecation of enable_confidential_logging"""

    compliant_logging.enable_confidential_logging()

    # https://docs.pytest.org/en/stable/capture.html
    stderr = capsys.readouterr().err
    assert (
        "SystemLog: The function enable_confidential_logging() is on the way "
        "to deprecation. Please use enable_compliant_logging() instead." in stderr
    )
