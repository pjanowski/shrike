# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
This script is designed to convert a repo/file based on aml-ds-pipeline-contrib,
confidential-ml-utils, and aml-build-tooling to adopt the shrike package in place.
"""
import os
import re
import argparse
import logging

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_path", required=True, help="Path to folder/file to be converted"
    )

    args = parser.parse_args()

    cur_repo_path = os.path.abspath(args.input_path)
    logger.info(f"Task: converting: {cur_repo_path}")

    # dash connected package name usually appears in requirements.txt or env.yaml
    keyword_pair = {
        "amldspipelinecontrib": "shrike.pipeline",
        "confidential_ml_utils": "shrike.confidential_logging",
        "aml_build_tooling": "shrike.build",
    }

    if os.path.isfile(cur_repo_path):
        logger.info(f"Converting {cur_repo_path}.")
        convert_file(keyword_pair, cur_repo_path)
    else:
        for root, dirs, files in os.walk(cur_repo_path):
            for file in files:
                input_path = os.path.join(root, file)
                logger.info(f"Converting {input_path}.")
                try:
                    convert_file(keyword_pair, input_path)
                    logger.info(f"Converting {input_path} successfully.")
                except Exception as e:
                    logger.error(
                        f"Unable to convert {input_path} with exception {e}. Please convert it manually."  # noqa
                    )


def check_is_requirements_file(file):
    root = os.path.split(file)[-1]
    if root.startswith("requirements-") or root == "requirements.txt":
        return True
    return False


def convert_file(keyword_pair, file):
    installed_shrike = False
    is_requirements_file = check_is_requirements_file(file)
    with open(file, "r") as input_file:
        lines = input_file.readlines()

    with open(file, "w") as output_file:
        for line in lines:
            if file.endswith((".py", ".yaml", ".yml")):
                for old_keyword in keyword_pair:
                    line = line.replace(old_keyword, keyword_pair[old_keyword])

            if file.endswith((".yml", ".yaml", "Dockerfile")) or is_requirements_file:
                if "Pip Authenticate aml-ds-pipeline-contrib" not in line:
                    line = re.sub(
                        "aml-ds-pipeline-contrib(==|~=)([0-9\.a-zA-Z])+",  # noqa
                        "shrike",
                        line,
                    )  # replace "aml-ds-pipeline-contrib==" or "~=" by shrike
                    line = re.sub(
                        "(aml-ds-pipeline-contrib)([^-]|$)", "shrike\g<2>", line  # noqa
                    )  # use case: when "aml-ds-pipeline-contrib-feed", do not replace

                    line = re.sub(
                        "aml-build-tooling((==|~=)([0-9\.a-zA-Z])+|$)",  # noqa
                        "shrike",
                        line,
                    )
                    line = re.sub(
                        "confidential-ml-utils((==|~=)([0-9\.a-zA-Z])+|$)",  # noqa
                        "shrike",
                        line,
                    )

            # list "shrike" only once in requirements.txt
            if is_requirements_file:
                if installed_shrike and "shrike" in line:
                    continue
                else:
                    output_file.write(line)
                    installed_shrike = "shrike" in line
            elif "pip install shrike" in line:
                if installed_shrike and "pip install shrike" in line:
                    continue
                else:
                    output_file.write(line)
                    installed_shrike = "pip install shrike" in line
            else:
                output_file.write(line)


if __name__ == "__main__":
    main()
