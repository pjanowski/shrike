"""Ran before all unittests in directory, initializes shared global variables"""
import os
import pytest
import tempfile


@pytest.fixture()
def pipeline_config_path():
    """Locates the pipeline config folder for unit tests.

    Returns:
        str: path to config file in temporary folder
    """
    return os.path.join(os.path.dirname(__file__), "sample", "conf")


@pytest.fixture()
def temporary_directory():
    """Path to temporary directory, deleted and recreated for each test.

    Returns:
        str: path to a temporary directory
    """
    temp_directory = tempfile.TemporaryDirectory()
    yield temp_directory.name
    temp_directory.cleanup()
