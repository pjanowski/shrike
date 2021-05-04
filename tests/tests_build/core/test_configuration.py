from shrike.build.core.configuration import load_configuration_from_args_and_env


def test_load_configuration_from_args_and_env_respects_args():
    args = ["--verbose", "--use-build-number"]
    config = load_configuration_from_args_and_env(
        args, {"BUILD_SOURCEBRANCH": "refs/heads/main", "BUILD_BUILDNUMBER": "1.1.1"}
    )
    assert config.verbose == True
    assert config.use_build_number == True
    assert config.all_component_version == "1.1.1"


def test_load_configuration_all_component_version(caplog):
    args = ["--all-component-version", "2.2.2"]
    with caplog.at_level("INFO"):
        config = load_configuration_from_args_and_env(args, {})
    assert config.all_component_version == "2.2.2"


def test_build_number_overwrite_all_component_version(caplog):
    args = ["--use-build-number", "--all-component-version", "2.2.2"]
    with caplog.at_level("INFO"):
        config = load_configuration_from_args_and_env(
            args,
            {"BUILD_SOURCEBRANCH": "refs/heads/main", "BUILD_BUILDNUMBER": "1.1.1"},
        )
    assert config.use_build_number == True
    assert config.all_component_version == "1.1.1"
    assert (
        "The build number 1.1.1 overwrites the value of all_component_version 2.2.2"
        in caplog.text
    )


def test_both_args_and_file(tmp_path):
    config_path = tmp_path / "aml-build-configuration.yml"
    config_path.write_text("verbose: False")

    args = [
        "--configuration-file",
        str(config_path),
        "--component-specification-glob",
        "*.yaml",
    ]

    config = load_configuration_from_args_and_env(
        args, {"BUILD_SOURCEBRANCH": "refs/heads/main"}
    )

    assert config.configuration_file == str(config_path)
    assert config.component_specification_glob == "*.yaml"
    assert config.verbose == False


def test_configuration_file_alone_works_fine(tmp_path):
    config_path = tmp_path / "aml-build-configuration.yml"
    config_path.write_text("use_build_number: True\nall_component_version: 0.0.0")

    args = ["--configuration-file", str(config_path)]

    # Assert: does not raise.
    config = load_configuration_from_args_and_env(
        args, {"BUILD_SOURCEBRANCH": "refs/heads/main", "BUILD_BUILDNUMBER": "x.x.x"}
    )

    assert config.use_build_number == True
    assert config.all_component_version == "x.x.x"


def test_load_configuration_from_args_and_env_deprecation(caplog, tmp_path):
    config_path = tmp_path / "aml-build-configuration.yml"
    config_path.write_text("fail_if_version_exists: True")
    args1 = ["--allow-duplicate-versions"]
    args2 = ["--allow-duplicate-versions", "--fail-if-version-exists"]
    args3 = ["--allow-duplicate-versions", "--configuration-file", str(config_path)]
    args4 = ["--configuration-file", str(config_path)]

    with caplog.at_level("INFO"):
        config1 = load_configuration_from_args_and_env(args1, {})

    assert config1.fail_if_version_exists == False
    assert "We recommend against" in caplog.text
    assert "Please refer to" in caplog.text

    config2 = load_configuration_from_args_and_env(args2, {})
    assert config2.fail_if_version_exists

    config3 = load_configuration_from_args_and_env(args3, {})
    assert config3.fail_if_version_exists

    config4 = load_configuration_from_args_and_env(args4, {})
    assert config4.fail_if_version_exists
