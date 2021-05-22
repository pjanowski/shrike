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


def check_is_target_file(file):
    if file.endswith((".py", ".yaml", ".yml", "Dockerfile")):
        return True
    elif check_is_requirements_file(file):
        return True
    else:
        return False


def check_is_requirements_file(file):
    root = os.path.split(file)[-1]
    if root.startswith("requirements-") or root == "requirements.txt":
        return True
    return False


def convert_file(keyword_pair, file):
    is_requirements_file = check_is_requirements_file(file)
    with open(file, "r", encoding="utf8") as input_file:
        lines = input_file.readlines()

    with open(file, "w", encoding="utf8") as output_file:
        for line in lines:
            if file.endswith((".py", ".yaml", ".yml")):
                for old_keyword in keyword_pair:
                    line = line.replace(old_keyword, keyword_pair[old_keyword])

            if file.endswith((".yml", ".yaml", "Dockerfile")) or is_requirements_file:
                if "Pip Authenticate aml-ds-pipeline-contrib" not in line:
                    # Replace the line of
                    # "pip install aml-ds-pipeline-contrib==0.1.9 --extra-index-url
                    # https://azuremlsdktestpypi.azureedge.net/modulesdkpreview"
                    # by "shrike[pipeline]"
                    line = re.sub(
                        "pip install aml-ds-pipeline-contrib(==|~=)([0-9\.\ \-\:\/a-zA-Z])+",  # noqa
                        "pip install shrike[pipeline]",
                        line,
                    )
                    # Replace "aml-ds-pipeline-contrib==" or "~=" by shrike
                    line = re.sub(
                        "aml-ds-pipeline-contrib(==|~=)([0-9\.a-zA-Z])+",  # noqa
                        "shrike[pipeline]",
                        line,
                    )
                    # Use case: when "aml-ds-pipeline-contrib-feed", do not replace
                    line = re.sub(
                        "(aml-ds-pipeline-contrib)([^-]|$)", "shrike\g<2>", line  # noqa
                    )
                    line = re.sub(
                        "aml-build-tooling((==|~=)([0-9\.a-zA-Z])+|$)",  # noqa
                        "shrike[build]",
                        line,
                    )
                    line = re.sub(
                        "confidential-ml-utils((==|~=)([0-9\.a-zA-Z])+|$)",  # noqa
                        "shrike",
                        line,
                    )

            output_file.write(line)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_path", required=True, help="Path to folder/file to be converted"
    )

    args = parser.parse_args()

    cur_repo_path = os.path.abspath(args.input_path)
    logger.info(f"Task: converting: {cur_repo_path}")

    keyword_pair = {
        "amldspipelinecontrib": "shrike.pipeline",
        "confidential_ml_utils": "shrike.compliant_logging",
        "aml_build_tooling": "shrike.build",
        "confidential_logging": "compliant_logging",
        "ConfidentialLogger": "CompliantLogger",
    }

    if os.path.isfile(cur_repo_path):
        logger.info(f"Converting {cur_repo_path}.")
        convert_file(keyword_pair, cur_repo_path)
    else:
        for root, dirs, files in os.walk(cur_repo_path):
            for file in files:
                input_path = os.path.join(root, file)
                if check_is_target_file(input_path):
                    logger.info(f"Converting {input_path}.")
                    try:
                        convert_file(keyword_pair, input_path)
                        logger.info(f"Converting {input_path} successfully.")
                    except Exception as e:
                        logger.error(
                            f"Unable to convert {input_path} with exception {e}. Please convert it manually."  # noqa
                        )


if __name__ == "__main__":
    main()
