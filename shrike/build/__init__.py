# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Tooling for making it easy to create Azure DevOps build pipelines for
validating, "building", signing, and registering components in eyes-off
Azure Machine Learning workspaces.
"""

from .commands import prepare, register
