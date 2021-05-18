# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Utilities around logging data which may or may not contain private content.
"""


from typing import Optional
from shrike.compliant_logging.constants import DataCategory
import logging
import sys
from threading import Lock


_LOCK = Lock()
_PREFIX = None


def set_prefix(prefix: str) -> None:
    """
    Set the global prefix to use when logging public (non-private) data.

    This method is thread-safe.
    """
    with _LOCK:
        global _PREFIX
        _PREFIX = prefix


def get_prefix() -> Optional[str]:
    """
    Obtain the current global prefix to use when logging public (non-private)
    data.
    """
    return _PREFIX


class CompliantLogger(logging.getLoggerClass()):  # type: ignore
    """
    Subclass of the default logging class with an explicit `category` parameter
    on all logging methods. It will pass an `extra` param with `prefix` key
    (value depending on whether `category` is public or private) to the
    handlers.

    The default value for data `category` is `PRIVATE` for all methods.

    Implementation is inspired by:
    https://github.com/python/cpython/blob/3.8/Lib/logging/__init__.py
    """

    def __init__(self, name: str):
        super().__init__(name)  # type: ignore

    def _log(
        self,
        level,
        msg,
        args=None,
        exc_info=None,
        extra=None,
        stack_info=False,
        stacklevel=1,
        category=DataCategory.PRIVATE,
    ):
        p = ""
        if category == DataCategory.PUBLIC:
            p = get_prefix()
        if extra:
            extra.update({"prefix": p})
        else:
            extra = {"prefix": p}
        if sys.version_info[1] <= 7:
            super(CompliantLogger, self)._log(
                level=level,
                msg=msg,
                args=args,
                exc_info=exc_info,
                extra=extra,
                stack_info=stack_info,
            )
        else:
            super(CompliantLogger, self)._log(
                level=level,
                msg=msg,
                args=args,
                exc_info=exc_info,
                extra=extra,
                stack_info=stack_info,
                stacklevel=stacklevel,  # type: ignore
            )


_logging_basic_config_set_warning = """
********************************************************************************
The root logger already has handlers set! As a result, the behavior of this
library is undefined. If running in Python >= 3.8, this library will attempt to
call logging.basicConfig(force=True), which will remove all existing root
handlers. See https://stackoverflow.com/q/20240464 and
https://github.com/Azure/confidential-ml-utils/issues/33 for more information.
********************************************************************************
"""


def enable_compliant_logging(prefix: str = "SystemLog:", **kwargs) -> None:
    """
    The default format is `logging.BASIC_FORMAT` (`%(levelname)s:%(name)s:%(message)s`).
    All other kwargs are passed to `logging.basicConfig`. Sets the default
    logger class and root logger to be compliant. This means the format
    string `%(prefix)` will work.

    Set the format using the `format` kwarg.

    If running in Python >= 3.8, will attempt to add `force=True` to the kwargs
    for logging.basicConfig.

    After calling this method, use the kwarg `category` to pass in a value of
    `DataCategory` to denote data category. The default is `PRIVATE`. That is,
    if no changes are made to an existing set of log statements, the log output
    should be the same.

    The standard implementation of the logging API is a good reference:
    https://github.com/python/cpython/blob/3.9/Lib/logging/__init__.py
    """
    set_prefix(prefix)

    if "format" not in kwargs:
        kwargs["format"] = f"%(prefix)s{logging.BASIC_FORMAT}"

    # Ensure that all loggers created via `logging.getLogger` are instances of
    # the `CompliantLogger` class.
    logging.setLoggerClass(CompliantLogger)

    if len(logging.root.handlers) > 0:
        p = get_prefix()
        for line in _logging_basic_config_set_warning.splitlines():
            print(f"{p}{line}", file=sys.stderr)

    if "force" not in kwargs and sys.version_info >= (3, 8):
        kwargs["force"] = True

    old_root = logging.root

    root = CompliantLogger(logging.root.name)
    root.handlers = old_root.handlers

    logging.root = root
    logging.Logger.root = root  # type: ignore
    logging.Logger.manager = logging.Manager(root)  # type: ignore

    # https://github.com/kivy/kivy/issues/6733
    logging.basicConfig(**kwargs)


def enable_confidential_logging(prefix: str = "SystemLog:", **kwargs) -> None:
    """
    This function is a duplicate of the function `enable_compliant_logging`.
    We encourage users to use `enable_compliant_logging`.
    """
    print(
        f"{prefix} The function enable_confidential_logging() is on the way"
        " to deprecation. Please use enable_compliant_logging() instead.",
        file=sys.stderr,
    )
    enable_compliant_logging(prefix, **kwargs)
