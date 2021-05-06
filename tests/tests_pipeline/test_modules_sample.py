# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
PyTest suite for testing if each run.py is aligned with module specification:

> Status: this code relates to the _recipe_ and is a _proposition_
"""
import pytest
import os

from shrike.pipeline.testing.module_run_tests import module_run_get_arg_parser
from shrike.pipeline.testing.module_run_tests import (
    if_arguments_from_module_spec_match_script_argparse,
)
from shrike.pipeline.testing.module_run_tests import run_py_import
from shrike.pipeline.testing.module_run_tests import (
    module_spec_yaml_exists_and_is_parsable,
)

# from shrike.pipeline.testing.module_run_tests import (
#    script_main_with_synthetic_arguments,
# )
from shrike.pipeline.testing.module_run_tests import module_uses_private_acr
from shrike.pipeline.testing.module_run_tests import (
    module_uses_private_python_feed,
)

# modules that should ALSO pass advanced tests (design pattern)
MODULE_STEP_FOLDERS = [
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "sample", "steps", "stats_passthrough")
    ),
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "sample",
            "steps",
            "stats_passthrough_windows",
        )
    ),
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "sample", "steps", "multinode_trainer")
    ),
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "sample", "steps", "spark_hello")
    ),
    # os.path.abspath(
    #     os.path.join(os.path.dirname(__file__), "sample", "steps", "convert_tsv_to_ss")
    # )
]

### BASIC TESTS ###
# for basic module designs (minimal wrappers)


@pytest.mark.parametrize("module", MODULE_STEP_FOLDERS)
def test_run_py_import(module):
    """Try importing run.py, just to check if basic script passes syntax/imports checks"""
    run_py_import(module)


@pytest.mark.parametrize("module", MODULE_STEP_FOLDERS)
def test_module_spec_yaml_exists_and_is_parsable(module):
    """Try loading the module_spec.yaml file for the module"""
    module_spec_yaml_exists_and_is_parsable(module)


### ADVANCED TESTS ###
# for module implementing full design pattern (get_arg_parser())


@pytest.mark.parametrize("module", MODULE_STEP_FOLDERS)
def test_module_run_get_arg_parser(module):
    """Tests is module run.py has function get_arg_parser(parser)"""
    module_run_get_arg_parser(module)


@pytest.mark.parametrize("module", MODULE_STEP_FOLDERS)
def test_module_spec_args_against_script_argparse(module):
    """Tests alignment between module_spec arguments and script parser arguments"""
    if_arguments_from_module_spec_match_script_argparse(module)


# NOTE: this test has been disabled because it requires exception re-throw in compliant_handle()
# see pull request https://eemo.visualstudio.com/TEE/_git/TEEGit/pullrequest/16849
# @pytest.mark.parametrize("module", MODULE_MANIFEST_ADVANCED)
# def test_script_main_with_synthetic_arguments(mocker, module):
#    """Tests alignment between module_spec arguments and script parser arguments"""
#    script_main_with_synthetic_arguments(module, mocker)

### COMPLIANCE TESTS (EXPERIMENTAL) ###
# for modules running in Heron eyes-off environment


@pytest.mark.parametrize("module", MODULE_STEP_FOLDERS)
def test_module_uses_private_acr(module):
    """Tests base image in private ACR"""
    module_uses_private_acr(module, "polymerprod.azurecr.io")


@pytest.mark.parametrize("module", MODULE_STEP_FOLDERS)
def test_module_uses_private_python_feed(module):
    """Tests base image in private python feed"""
    module_uses_private_python_feed(
        module,
        "https://o365exchange.pkgs.visualstudio.com/_packaging/PolymerPythonPackages/pypi/simple/",
    )
