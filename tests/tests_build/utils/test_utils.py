# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pathlib import Path
import pytest
import logging

from shrike.build.utils import utils


@pytest.mark.parametrize(
    "file_name,expected_hash",
    [
        ("run.py", "23715807DA0DE9F473FDE6A2AF9E1CF9A769EBD4E3E32659B10212972230BDDB"),
        (
            ".amlignore",
            "183C6C201CD9FC9C8D84FC40D1E496AC3716C4B31B5342F6B8659DA5949F1B45",
        ),
    ],
)
def test_create_SHA_256_hash_of_file_matches_cosmic_build_tool(
    file_name, expected_hash
):
    """
    Cross-check the local "SHA 256 hash" implementation against the "Cosmic"
    build tool. These hashes were obtained from the build:

    https://dev.azure.com/msdata/Vienna/_build/results?buildId=29991141&view=artifacts&pathAsName=false&type=publishedArtifacts
    """
    file_path = str(Path(__file__).parent.parent / "steps" / file_name)
    hash = utils.create_SHA_256_hash_of_file(file_path)
    print(hash)

    assert hash == expected_hash


def test_telemetry_logger(caplog):
    """Unit tests for utils class of opencensus azure monitor"""
    telemetry_logger = utils.TelemetryLogger()
    assert (
        telemetry_logger.instrumentation_key == "aaefce9e-d109-4fac-bb9f-8277c68e91ac"
    )
    assert telemetry_logger.enable_telemetry

    telemetry_logger = utils.TelemetryLogger(enable_telemetry=False)
    assert not telemetry_logger.enable_telemetry
    with caplog.at_level("INFO"):
        telemetry_logger.log_trace(message="A unit test message. Please ignore it.")
    assert (
        "Sending trace log messages to application insight has been disabled."
        in caplog.text
    )

    telemetry_logger = utils.TelemetryLogger(enable_telemetry=True)
    telemetry_logger.log_trace(
        message="A unit test message. Please ignore it.", level=logging.INFO
    )
