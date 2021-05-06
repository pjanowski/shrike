# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
PyTest suite for testing if each run.py is aligned with module specification:

> Status: this code relates to the _recipe_ and is a _proposition_
"""
import pytest
import os

from shrike.pipeline.testing.components import (
    component_spec_yaml_exists_and_is_parsable,
)
from shrike.pipeline.testing.components import component_uses_private_acr
from shrike.pipeline.testing.components import component_uses_private_python_feed
from shrike.pipeline.testing.components import component_run_py_import
from shrike.pipeline.testing.components import component_run_get_arg_parser
from shrike.pipeline.testing.components import (
    if_arguments_from_component_spec_match_script_argparse,
)

COMPONENT_ROOT_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "sample", "steps")
)

# modules that should ALSO pass advanced tests (design pattern)
COMPONENT_FOLDERS = [
    "stats_passthrough",
    "stats_passthrough_windows",
    "multinode_trainer",
    "spark_hello",
]

COMPONENT_FILE_NAME = "module_spec.yaml"  # old style naming convention

### BASIC TESTS ###
# for basic module designs (minimal wrappers)


@pytest.mark.parametrize("component_folder", COMPONENT_FOLDERS)
def test_component_run_py_import(component_folder):
    """Try importing run.py, just to check if basic script passes syntax/imports checks"""
    component_run_py_import(
        os.path.join(COMPONENT_ROOT_FOLDER, component_folder, COMPONENT_FILE_NAME)
    )


@pytest.mark.parametrize("component_folder", COMPONENT_FOLDERS)
def test_component_spec_yaml_exists_and_is_parsable(component_folder):
    """Try loading and parsing the component spec yaml file"""
    component_spec_yaml_exists_and_is_parsable(
        os.path.join(COMPONENT_ROOT_FOLDER, component_folder, COMPONENT_FILE_NAME)
    )


### ADVANCED TESTS ###
# for module implementing full design pattern (get_arg_parser())


@pytest.mark.parametrize("component_folder", COMPONENT_FOLDERS)
def test_component_run_get_arg_parser(component_folder):
    """Tests if component run.py has function get_arg_parser(parser)"""
    component_run_get_arg_parser(
        os.path.join(COMPONENT_ROOT_FOLDER, component_folder, COMPONENT_FILE_NAME)
    )


@pytest.mark.parametrize("component_folder", COMPONENT_FOLDERS)
def test_if_arguments_from_component_spec_match_script_argparse(component_folder):
    """Tests alignment between module_spec arguments and script parser arguments"""
    if_arguments_from_component_spec_match_script_argparse(
        os.path.join(COMPONENT_ROOT_FOLDER, component_folder, COMPONENT_FILE_NAME)
    )


# NOTE: this test has been disabled because it requires exception re-throw in compliant_handle()
# see pull request https://eemo.visualstudio.com/TEE/_git/TEEGit/pullrequest/16849
# @pytest.mark.parametrize("module", MODULE_MANIFEST_ADVANCED)
# def test_script_main_with_synthetic_arguments(mocker, module):
#    """Tests alignment between module_spec arguments and script parser arguments"""
#    script_main_with_synthetic_arguments(module, mocker)

### COMPLIANCE TESTS (EXPERIMENTAL) ###
# for modules running in Heron eyes-off environment


@pytest.mark.parametrize("component_folder", COMPONENT_FOLDERS)
def test_component_uses_private_acr(component_folder):
    """Tests base image in private ACR"""
    component_uses_private_acr(
        os.path.join(COMPONENT_ROOT_FOLDER, component_folder, COMPONENT_FILE_NAME),
        "polymerprod.azurecr.io",
    )


@pytest.mark.parametrize("component_folder", COMPONENT_FOLDERS)
def test_component_uses_private_python_feed(component_folder):
    """Tests base image in private python feed"""
    component_uses_private_python_feed(
        os.path.join(COMPONENT_ROOT_FOLDER, component_folder, COMPONENT_FILE_NAME),
        "https://o365exchange.pkgs.visualstudio.com/_packaging/PolymerPythonPackages/pypi/simple/",
    )
