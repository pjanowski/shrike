"""
Unit tests for the `prepare` module.

Consider decorating long end-to-end tests with `@pytest.mark.order(-1)`.
"""

import pytest
import os
from pathlib import Path
import subprocess
import shutil
import yaml

from shrike.build.commands import prepare
from shrike.build.core.configuration import Configuration


def clean() -> None:
    """
    Clean up all non checked-in files.
    """
    subprocess.run(["git", "clean", "-xdf"])


@pytest.mark.order(-1)
def test_build_all_components(caplog):
    prep = prepare.Prepare()
    prep.config = Configuration(signing_mode="foo")
    prep.ensure_component_cli_installed()
    component = "tests/tests_build/steps/spec.yaml"
    with caplog.at_level("INFO"):
        success = prep.build_all_components([component])
    assert success
    assert f"Component {component} is built." in caplog.text


@pytest.mark.parametrize("mode", ["foo", "aether", "aml"])
def test_find_component_specification_files_using_all(mode):
    # clean the .build directories first, such that we won't include the
    # spec.yaml files under .build directories in the unit tests here
    clean()

    prep = prepare.Prepare()
    prep.config = Configuration(signing_mode=mode)

    dir = str(Path(__file__).parent.parent.resolve() / "steps/component1")
    print(dir)
    res = prep.find_component_specification_files_using_all(dir=dir)
    print("found spec yaml file paths list: ", res)
    assert len(res) == 1

    dir = str(Path(__file__).parent.parent / "steps/component1")
    print(dir)
    res = prep.find_component_specification_files_using_all(dir=dir)
    print("found spec yaml file paths list: ", res)
    assert len(res) == 1

    dir = str(Path(__file__).parent.parent.resolve() / "steps/component2")
    print(dir)
    res = prep.find_component_specification_files_using_all(dir=dir)
    print("found spec yaml file paths list: ", res)
    assert len(res) == 1

    dir = str(Path(__file__).parent.parent / "steps/component2")
    print(dir)
    res = prep.find_component_specification_files_using_all(dir=dir)
    print("found spec yaml file paths list: ", res)
    assert len(res) == 1

    dir = str(Path(__file__).parent.parent.resolve() / "steps/component3")
    print(dir)
    res = prep.find_component_specification_files_using_all(dir=dir)
    print("found spec yaml file paths list: ", res)
    assert len(res) == 1

    dir = str(Path(__file__).parent.parent / "steps/component3")
    print(dir)
    res = prep.find_component_specification_files_using_all(dir=dir)
    print("found spec yaml file paths list: ", res)
    assert len(res) == 1

    dir = str(Path(__file__).parent.parent.resolve() / "steps")
    print(dir)
    res = prep.find_component_specification_files_using_all(dir=dir)
    print("found spec yaml file paths list: ", res)
    assert len(res) == 5

    dir = str(Path(__file__).parent.parent / "steps")
    print(dir)
    res = prep.find_component_specification_files_using_all(dir=dir)
    print("found spec yaml file paths list: ", res)
    assert len(res) == 5


def test_create_catalog_files_fails_if_non_standard_mode():
    with pytest.raises(ValueError):
        prep = prepare.Prepare()
        prep.config = Configuration(signing_mode="foo")
        prep.create_catalog_files([""])


def test_create_catalog_files_fails_if_non_standard():
    with pytest.raises(ValueError):
        prep = prepare.Prepare()
        prep.config = Configuration(signing_mode="foo")
        prep.create_catalog_files(
            [
                "tests/tests_build/steps/component1/spec.yaml",
                "tests/tests_build/steps/component2/spec.yaml",
            ]
        )


def test_non_standard_activation_method_not_supported():
    with pytest.raises(ValueError):
        prep = prepare.Prepare()
        prep.config = Configuration(activation_method="foo")
        prep.find_component_specification_files()


def test_smart_method_not_supported():
    with pytest.raises(NotImplementedError):
        prep = prepare.Prepare()
        prep.find_component_specification_files_using_smart()
    with pytest.raises(NotImplementedError):
        prep = prepare.Prepare()
        prep.config = Configuration(activation_method="smart")
        prep.find_component_specification_files()


def test_create_catalog_files_for_aether(caplog):
    prep = prepare.Prepare()
    prep.config = Configuration(signing_mode="aether")
    prep.ensure_component_cli_installed()
    component = [
        "tests/tests_build/steps/component1/spec.yaml",
        "tests/tests_build/steps/component2/spec.yaml",
    ]
    with caplog.at_level("INFO"):
        prep.create_catalog_files_for_aether(component)
    assert "Finish creating aether catalog files for component1." in caplog.text
    assert "Finish creating aether catalog files for component2." in caplog.text
    assert os.path.exists("tests/tests_build/steps/component1/component1.cat")
    assert os.path.exists("tests/tests_build/steps/component2/component2.cat")
    os.remove("tests/tests_build/steps/component1/component1.cat")
    os.remove("tests/tests_build/steps/component2/component2.cat")


@pytest.mark.order(-1)
def test_ensure_component_cli_installed(caplog):
    prep = prepare.Prepare()
    prep.config = Configuration(activation_method="foo")
    with caplog.at_level("INFO"):
        first_try = prep.ensure_component_cli_installed()
        second_try = prep.ensure_component_cli_installed()

    assert second_try == True
    assert "component CLI exists. Skipping installation." in caplog.text


@pytest.mark.order(-1)
def test_log_info_component_cli_installed(caplog):
    prep = prepare.Prepare()
    prep.config = Configuration(activation_method="foo")
    with caplog.at_level("ERROR"):
        prep.ensure_component_cli_installed()
    assert "Command failed with exit code" not in caplog.text


@pytest.mark.parametrize("catalog_file_name", ["catalog.json", "catalog.json.sig"])
def test_create_catalog_files_for_aml(catalog_file_name):
    prep = prepare.Prepare()
    # we'll test 2 component folder structures
    component1_folder = "tests/tests_build/steps/component1/"  # flat directory
    component2_folder = "tests/tests_build/steps/component2/"  # nested directories
    # create the catalogs
    prep.create_catalog_files_for_aml(
        [
            os.path.join(component1_folder, "spec.yaml"),
            os.path.join(component2_folder, "spec.yaml"),
        ]
    )
    # grab the freshly created catalogs
    component1_catalog_path = os.path.join(component1_folder, catalog_file_name)
    with open(component1_catalog_path, "r") as component1_catalog_file:
        component1_catalog_contents = component1_catalog_file.read()
    component2_catalog_path = os.path.join(component2_folder, catalog_file_name)
    with open(component2_catalog_path, "r") as component2_catalog_file:
        component2_catalog_contents = component2_catalog_file.read()
    # hard-coded values to check
    component1_catalog_reference = '{"HashAlgorithm": "SHA256", "CatalogItems": {"another_file_for_component1.txt": "9E640A18FC586A6D87716F9B4C6728B7023819E58E07C4562E0D2C14DFC3CF5B", "spec.yaml": "BF41A2F4D427A281C0E7EB5F987E285D69F5D50AEFCBB559DC2D7611D861D7FA"}}'
    component2_catalog_reference = '{"HashAlgorithm": "SHA256", "CatalogItems": {".amlignore": "1CA13EBDBB24D532673E22A0886631976CDC9B9A94488FE31AF9214F4A79E8AE", ".subdir/.gitignore": "A5270F91138FC2BB5470ECB521DAB043140D7E0FD8CB33BB0644AC13EFB60FE7", "another_file_for_component2.txt": "A47275ACA3BC482FC3F4C922572EA514D0DE03EA836597D34FC21BA805D2ABCA", "spec.yaml": "CEB85EE73A9084A8C778325596A3222E04F70E06A048F2072D11E9BC6E15BADA", "subdir1/.gitignore": "C0159813AB6EAF3CC8A0BD37C79E4CDD927E3E95CB9BA8EC246BC3A176C3EB41", "subdir1/file_in_subdir1.txt": "A7917FCCF0C714716F308967DB45B2DDEE4665FC4B4FCC6C0E50ABD55DD1C6B5", "subdir1/subsubdir1/file_in_subsubdir1.txt": "1791DD6583A06429603CC30CDC2AE6A217853722C6BB10AA31027F5A931D5A7D", "subdir2/file_in_subdir2.txt": "419EE822D1E34B22FCE7F09EDCFC7565188A1362352E1DADB569820CB599D651"}}'
    # assertions
    assert component1_catalog_contents == component1_catalog_reference
    assert component2_catalog_contents == component2_catalog_reference


def test_validate_all_components_does_nothing_if_no_files(caplog):
    prep = prepare.Prepare()

    with caplog.at_level("INFO"):
        prep.validate_all_components([])

    assert not caplog.text


@pytest.mark.order(-1)
def test_validate_all_components_works_on_invalid_component():
    component_path = str(
        Path(__file__).parent.parent.resolve() / "steps/component1/spec.yaml"
    )

    prep = prepare.Prepare()
    prep.config = Configuration()

    prep.attach_workspace(
        "/subscriptions/48bbc269-ce89-4f6f-9a12-c6f91fcb772d/resourceGroups/aml1p-rg/providers/Microsoft.MachineLearningServices/workspaces/aml1p-ml-canary"
    )
    success = prep.validate_all_components([component_path])

    assert not success
    assert prep._component_statuses[component_path]["validate"] == "failed"
    assert len(prep._errors) == 1


@pytest.mark.order(-1)
def test_validate_all_components_works_on_valid_component(caplog):
    component_path = str(
        Path(__file__).parent.parent.resolve() / "steps/component2/spec.yaml"
    )

    prep = prepare.Prepare()
    prep.config = Configuration()

    prep.attach_workspace(
        "/subscriptions/48bbc269-ce89-4f6f-9a12-c6f91fcb772d/resourceGroups/aml1p-rg/providers/Microsoft.MachineLearningServices/workspaces/aml1p-ml-canary"
    )

    with caplog.at_level("INFO"):
        prep.validate_all_components([component_path])

    assert prep._component_statuses[component_path]["validate"] == "succeeded"
    assert not prep._errors
    assert "is valid" in caplog.text


@pytest.mark.order(-1)
def test_validate_all_components_code_snapshot_parameter(caplog):
    tmp_dir = str(Path(__file__).parent.parent.resolve() / "steps/tmp_dir")
    tmp_yaml = {
        "$schema": "http://azureml/sdk-2-0/CommandComponent.json",
        "name": "dummy_component",
        "version": "0.0.1",
        "type": "CommandComponent",
        "command": "pip freeze",
        "code": "../../",
    }
    os.mkdir(tmp_dir)
    with open(tmp_dir + "/spec.yaml", "w") as tmp_spec:
        yaml.dump(tmp_yaml, tmp_spec)

    prep = prepare.Prepare()
    prep.config = Configuration()

    prep.attach_workspace(
        "/subscriptions/48bbc269-ce89-4f6f-9a12-c6f91fcb772d/resourceGroups/aml1p-rg/providers/Microsoft.MachineLearningServices/workspaces/aml1p-ml-canary"
    )

    with caplog.at_level("INFO"):
        prep.validate_all_components([tmp_dir + "/spec.yaml"])

    assert prep._component_statuses[tmp_dir + "/spec.yaml"]["validate"] == "failed"
    assert len(prep._errors) == 1
    assert (
        "Code snapshot parameter is not supported by aml-build-tooling. Please use .additional_includes for your component."
        in caplog.text
    )

    # Clean up tmp directory
    shutil.rmtree(tmp_dir)


@pytest.mark.order(-1)
def test_validate_all_components_code_Section(caplog):
    component_path = str(
        Path(__file__).parent.parent.resolve() / "steps/component4/spec.yaml"
    )

    prep = prepare.Prepare()
    prep.config = Configuration()

    prep.attach_workspace(
        "/subscriptions/48bbc269-ce89-4f6f-9a12-c6f91fcb772d/resourceGroups/aml1p-rg/providers/Microsoft.MachineLearningServices/workspaces/aml1p-ml-canary"
    )

    with caplog.at_level("INFO"):
        prep.validate_all_components([component_path])

    assert prep._component_statuses[component_path]["validate"] == "succeeded"
    assert not prep._errors
    assert "is valid" in caplog.text
    assert (
        "Code snapshot parameter is not supported by aml-build-tooling. Please use .additional_includes for your component."
        not in caplog.text
    )


@pytest.mark.order(-1)
def test_workspace_attachment_for_invalid_workspace(caplog):
    prep = prepare.Prepare()
    prep.config = Configuration()

    # try to attach a fake (non-ecxisting) workspace. expected to receive a register_error message.
    fake_workspace_id = "/subscriptions/48bbc269-ce89-4f6f-9a12-c6f91fcb772d/resourceGroups/aml1p-rg/providers/Microsoft.MachineLearningServices/workspaces/aml1p-ml-canary-fake"
    with caplog.at_level("INFO"):
        prep.attach_workspace(fake_workspace_id)

    assert f"Error!! Failed to attach to {fake_workspace_id}!" in prep._errors
    assert f"Error!! Failed to attach to {fake_workspace_id}!" in caplog.text


@pytest.mark.order(-1)
def test_run_with_config_runs_end_to_end(caplog):
    prep = prepare.Prepare()
    prep.config = Configuration(
        workspaces=[
            "/subscriptions/48bbc269-ce89-4f6f-9a12-c6f91fcb772d/resourceGroups/aml1p-rg/providers/Microsoft.MachineLearningServices/workspaces/aml1p-ml-canary"
        ]
    )

    with caplog.at_level("INFO"):
        prep.run_with_config()

    assert "Running component preparation logic" in caplog.text


@pytest.mark.parametrize(
    "component,expected_len", [("component1", 2), ("component2", 8), ("component3", 1)]
)
def test_all_files_in_snapshot(component, expected_len):
    clean()

    directory = str(Path(__file__).parent.parent.resolve() / f"steps/{component}")
    prep = prepare.Prepare()
    result = prep.all_files_in_snapshot(f"{directory}/spec.yaml")
    assert len(result) == expected_len
