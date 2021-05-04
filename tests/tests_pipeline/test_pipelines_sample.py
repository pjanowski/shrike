"""
PyTest suite for testing all runnable pipelines.
"""
import os
import pytest
import sys
import tempfile
from unittest.mock import patch

from shrike.pipeline.testing.pipeline_class_test import (
    get_config_class,
    pipeline_required_modules,
    pipeline_required_subgraphs,
)
from .sample.pipeline.passthrough_test import CanaryPipelineStatsPassthrough
from .sample.pipeline.multinode_training_test import MultiNodeTrainingPipeline
from .sample.pipeline.spark_hello import SparkHelloPipeline

### Tests on the AMLPipelineHelper classes methods (unit tests)

PIPELINE_CLASSES = [
    CanaryPipelineStatsPassthrough,
    MultiNodeTrainingPipeline,
    SparkHelloPipeline,
]


@pytest.mark.parametrize("pipeline_class", PIPELINE_CLASSES)
def test_pipeline_classes_get_config_class(pipeline_class):
    """Test if the get_arg_parser() method is in there and behaves correctly"""
    get_config_class(pipeline_class)


@pytest.mark.parametrize("pipeline_class", PIPELINE_CLASSES)
def test_pipeline_classes_pipeline_required_modules(pipeline_class):
    """Test if the required_modules() returns the right list of modules with all required keys"""
    pipeline_required_modules(pipeline_class)


@pytest.mark.parametrize("pipeline_class", PIPELINE_CLASSES)
def test_pipeline_classes_pipeline_required_subgraphs(pipeline_class):
    """Tests if the required_subgraphs() returns the right list of modules with all requires keys"""
    pipeline_required_subgraphs(pipeline_class)


### Tests on the validation of pipeline (integration tests)


def test_passthrough_build_local(pipeline_config_path):
    """Tests the graph by running the main function itself (which does .validate())"""
    testargs = [
        "prog",
        "--config-dir",
        pipeline_config_path,
        "--config-name",
        "pipelines/passthrough_test",
        "module_loader.use_local='*'",
    ]
    # will do everything except submit :)
    with patch.object(sys, "argv", testargs):
        CanaryPipelineStatsPassthrough.main()


def test_passthrough_uuid_build_local(pipeline_config_path):
    """Tests the graph by running the main function itself (which does .validate())"""
    testargs = [
        "prog",
        "--config-dir",
        pipeline_config_path,
        "--config-name",
        "pipelines/passthrough_test_uuid",
        "module_loader.use_local='*'",
    ]
    # will do everything except submit :)
    with patch.object(sys, "argv", testargs):
        CanaryPipelineStatsPassthrough.main()


def test_multinode_training_build_local(pipeline_config_path):
    """Tests the graph by running the main function itself (which does .validate())"""
    testargs = [
        "prog",
        "--config-dir",
        pipeline_config_path,
        "--config-name",
        "pipelines/multinode_training_test",
        "module_loader.use_local='*'",
    ]
    # will do everything except submit :)
    with patch.object(sys, "argv", testargs):
        MultiNodeTrainingPipeline.main()


def test_spark_hello_build_local(pipeline_config_path):
    """Tests the graph by running the main function itself (which does .validate())"""
    testargs = [
        "prog",
        "--config-dir",
        pipeline_config_path,
        "--config-name",
        "pipelines/spark_hello_test",
        "module_loader.use_local='*'",
    ]
    # will do everything except submit :)
    with patch.object(sys, "argv", testargs):
        SparkHelloPipeline.main()
