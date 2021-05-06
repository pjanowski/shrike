# Shrike: Compliant Azure ML Utilities

[![CodeQL](https://github.com/Azure/shrike/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/Azure/shrike/actions/workflows/codeql-analysis.yml)
[![Component Governance](https://dev.azure.com/msdata/Vienna/_apis/build/status/aml-ds/Azure.shrike%20Component%20Governance?branchName=main)](https://dev.azure.com/msdata/Vienna/_build/latest?definitionId=16088&branchName=main)
[![ci-gate](https://dev.azure.com/msdata/Vienna/_apis/build/status/aml-ds/Azure.shrike%20ci-gate?branchName=main)](https://dev.azure.com/msdata/Vienna/_build/latest?definitionId=16115&branchName=main)
[![Python versions](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/Azure/shrike/branch/main/graph/badge.svg?token=sSq0BKlfTu)](https://codecov.io/gh/Azure/shrike)
[![license: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

Confidential ML is the practice of training machine learning models without
seeing the training data. It is needed in many enterprises to satisfy the
strict compliance and privacy guarantees they provide to their customers. This
repository contains a set of utilities for confidential ML, with a special
emphasis on using PyTorch in
[Azure Machine Learning pipelines](https://github.com/Azure/azureml-examples).
 
## Using

For more detailed examples and API reference, see the
[docs page]().

Minimal use case:

```python
from shrike.confidential_logging import DataCategory, enable_confidential_logging, prefix_stack_trace
import logging


@prefix_stack_trace(allow_list=["FileNotFoundError", "SystemExit", "TypeError"])
def main():
    enable_confidential_logging()

    log = logging.getLogger(__name__)
    log.info("Hi there", category=DataCategory.PUBLIC)

if __name__ == "__main__":
    main()
```

## Contributing

This project welcomes contributions and suggestions. Most contributions require
you to agree to a Contributor License Agreement (CLA) declaring that you have
the right to, and actually do, grant us the rights to use your contribution.
For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether
you need to provide a CLA and decorate the PR appropriately (e.g., status check,
comment). Simply follow the instructions provided by the bot. You will only need
to do this once across all repos using our CLA.

This project has adopted the
[Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the
[Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any
additional questions or comments.


## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft 
trademarks or logos is subject to and must follow 
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
