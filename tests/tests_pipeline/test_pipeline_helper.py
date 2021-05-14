# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Unit tests for pipeline_helper"""

import pytest
from shrike.pipeline.pipeline_helper import AMLPipelineHelper


def test_validate_experiment_name():
    """Unit tests for validate_experiment_name function"""
    with pytest.raises(ValueError):
        AMLPipelineHelper.validate_experiment_name("")
    with pytest.raises(ValueError):
        AMLPipelineHelper.validate_experiment_name("_exp-name")
    with pytest.raises(ValueError):
        AMLPipelineHelper.validate_experiment_name("wront.period")
    assert AMLPipelineHelper.validate_experiment_name("Correct-NAME_")
    assert AMLPipelineHelper.validate_experiment_name("ALLARELETTERS")
    assert AMLPipelineHelper.validate_experiment_name("12344523790")
