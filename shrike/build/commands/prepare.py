import itertools
import logging
import glob
from itertools import chain
import os
import collections
from typing import List, Tuple, Union
import shutil
from ruamel.yaml import YAML

from shrike.build.core.command_line import Command
from shrike.build.utils.utils import (
    create_catalog_stub,
    add_file_to_catalog,
    write_two_catalog_files,
    delete_two_catalog_files,
)
from pathlib import Path


log = logging.getLogger(__name__)


class Prepare(Command):
    def __init__(self):
        super().__init__()
        self._component_statuses = {}

    def folder_path(self, file: str) -> str:
        """
        Return the normalized path of the directory containing a file.
        """
        return self.normalize_path(Path(file).parent, directory=True)

    def all_files_in_snapshot(self, manifest: str) -> List[str]:
        """
        Return a list of all normalized files in the snapshot. The input
        (`manifest`) is assumed to be some file, whether AML-style component
        spec or Aether-style auto-approval manifest, in the "root" of the
        snapshot.
        """
        folder_path = self.folder_path(manifest)
        log.info("Absolute path for current component is: " + folder_path)

        # Generate a list of all files in this components folder (including subdirectories)
        rv = []

        # Make sure we pick up Linux-style "hidden" files like .amlignore and
        # hidden "directories", as well as hidden files in hidden directories.
        # https://stackoverflow.com/a/65205404
        # https://stackoverflow.com/a/41447012
        for root, _, file_paths in os.walk(folder_path):
            for file in file_paths:
                file_path = os.path.join(root, file)
                normalized_path = self.normalize_path(file_path)
                rv.append(normalized_path)

        return rv

    def build_all_components(self, files: List[str]) -> List[str]:
        """
        For each component specification file, run `az ml component build`,
        and register the status (+ register error if build failed). Returns the
        list of "built" component files.
        """
        rv = []

        for component in files:
            path = Path(component)
            rv.append(str(path.parent / ".build" / path.name))
            build_component_success = self.execute_azure_cli_command(
                f"ml component build --file {component}"
            )
            if build_component_success:
                log.info(f"Component {component} is built.")
            else:
                self.register_error(f"Error when building component {component}.")

        return rv

    def create_catalog_files(self, files: List[str]):
        """
        Create the appropriate kind of catalog file(s), using the configured
        method ("aml" or "aether").
        """
        signing_mode = self.config.signing_mode

        if signing_mode == "aml":
            self.create_catalog_files_for_aml(files)
        elif signing_mode == "aether":
            self.create_catalog_files_for_aether(files)
        else:
            raise ValueError(f"Invalid signing_mode provided: '{signing_mode}'")

    def create_catalog_files_for_aether(self, files: List[str]) -> None:
        """
        Create Aether-friendly .cat files, by first creating a CDF file, then
        finding and running `makecat.exe` to create the catalog file.
        """

        makecat_default = self.config.makecat_default
        makecat_directory = self.config.makecat_directory
        makecat = os.path.join(makecat_directory, makecat_default)

        if not os.path.exists(makecat):
            log.info(f"Default makecat location {makecat} does not exist")
            for path in Path(makecat_directory).rglob("makecat.exe"):
                if "x64" in str(path).lower():
                    makecat = path
                    break
        log.info(f"Makecat location: {makecat}")

        for file in files:

            directory = os.path.dirname(file)
            name = os.path.split(directory)[-1]
            cat_name = f"{name}.cat"
            cdf_name = f"{name}.cdf"
            path_to_cdf = os.path.join(directory, cdf_name)

            cdf_contents = f"""[CatalogHeader]
Name={cat_name}
PublicVersion=0x0000001
EncodingType=0x00010001
PageHashes=true
CATATTR1=0x00010001:OSAttr:2:6.2
[CatalogFiles]
"""
            files_in_module = self.all_files_in_snapshot(file)
            hash_lines = map(lambda p: f"<HASH>{p}={p}", files_in_module)
            all_hashes = "\n".join(hash_lines)
            cdf_contents += all_hashes

            log.info(f"CDF file contents:\n{cdf_contents}")

            with open(path_to_cdf, "w", encoding="ascii") as output:
                output.write(cdf_contents)

            success = self.execute_command([str(makecat), path_to_cdf, "-v"])
            if success:
                log.info(f"Creating Aether catalog files for {name} is successful.")
                shutil.move(cat_name, directory)
            else:
                self.register_error(
                    f"Error when creating Aether catalog files for {name}."
                )

            log.info(f"Removing {cdf_name}")
            os.remove(path_to_cdf)
            log.info(f"Finish creating aether catalog files for {name}.")

    def create_catalog_files_for_aml(self, files: List[str]) -> None:
        """
        Create AML-friendly catalog.json and catalog.json.sig files, using
        SHA-256 hash.
        """

        # For each component spec file in the input list, we'll do the following...
        for f in files:
            log.info(f"Processing file {f}")
            component_folder_path = self.folder_path(f)

            # remove catalog files if already present
            log.info("Deleting old catalog files if present")
            delete_two_catalog_files(component_folder_path)

            files_for_catalog = self.all_files_in_snapshot(f)
            log.info("The following list of files will be added to the catalog.")
            log.info(files_for_catalog)

            # Prepare the catlog stub: {'HashAlgorithm': 'SHA256', 'CatalogItems': {}}
            catalog = create_catalog_stub()

            # Add an entry to the catalog for each file
            for file_for_catalog in files_for_catalog:
                catalog = add_file_to_catalog(
                    file_for_catalog, catalog, component_folder_path
                )

            # order the CatalogItems dictionary
            catalog["CatalogItems"] = collections.OrderedDict(
                sorted(catalog["CatalogItems"].items())
            )

            # Write the 2 catalog files
            log.info(catalog)
            write_two_catalog_files(catalog, component_folder_path)
            log.info("Finished creating catalog files.")

    def find_component_specification_files(self) -> List[str]:
        """
        Find the list of "active" component specification files using the
        configured method ("all" or "smart").
        """
        activation_method = self.config.activation_method

        if activation_method == "all":
            rv = self.find_component_specification_files_using_all()
        elif activation_method == "smart":
            rv = self.find_component_specification_files_using_smart()
        else:
            raise ValueError(
                f"Invalid activation_method provided: '{activation_method}'"
            )

        return rv

    def find_component_specification_files_using_all(self, dir=None) -> List[str]:
        """
        Find all component specification files in the configured working
        directory matching the configured glob. Return the absolute paths
        of these files in the format of a list of string.
        """
        if dir is None:
            dir = self.config.working_directory
        all_spec_yaml_files_absolute_paths = [
            str(p.absolute())
            for p in Path(dir).glob(self.config.component_specification_glob)
        ]

        return all_spec_yaml_files_absolute_paths

    def find_component_specification_files_using_smart(self) -> List[str]:
        raise NotImplementedError(
            "Smart component activation/discovery method is not supported yet"
        )

    def run_with_config(self):
        log.info("Running component preparation logic.")

        self.telemetry_logging(command="prepare")

        component_files = self.find_component_specification_files()

        if self.config.signing_mode == "aml":
            self.ensure_component_cli_installed()
            self.attach_workspace()
            self.validate_all_components(component_files)
            built_component_files = self.build_all_components(component_files)
        else:
            built_component_files = component_files

        self.create_catalog_files(built_component_files)

    def validate_all_components(self, files: List[str]) -> None:
        """
        For each component specification file, run `az ml component validate`,
        and register the status (+ register error if validation failed).
        """
        for component in files:
            validate_component_success = self.execute_azure_cli_command(
                f"ml component validate --file {component}"
            )
            if validate_component_success:
                # If the az ml validation succeeds, we continue to check whether
                # the "code" snapshot parameter is specified in the spec file
                # https://componentsdk.z22.web.core.windows.net/components/component-spec-topics/code-snapshot.html
                with open(component, "r") as spec_file:
                    spec = YAML(typ="safe").load(spec_file)
                spec_code = spec.get("code")
                if spec_code and spec_code not in [".", "./"]:
                    self.register_component_status(component, "validate", "failed")
                    self.register_error(
                        "Code snapshot parameter is not supported by aml-build-tooling. Please use .additional_includes for your component."
                    )
                else:
                    log.info(f"Component {component} is valid.")
                    self.register_component_status(component, "validate", "succeeded")
            else:
                self.register_component_status(component, "validate", "failed")
                self.register_error(f"Error when validating component {component}.")


if __name__ == "__main__":
    Prepare().run()
