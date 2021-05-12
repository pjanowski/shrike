# Shrike: Compliant Azure ML Utilities

[![CodeQL](https://github.com/Azure/shrike/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/Azure/shrike/actions/workflows/codeql-analysis.yml)
[![docs](https://github.com/Azure/shrike/actions/workflows/docs.yml/badge.svg)](https://github.com/Azure/shrike/actions/workflows/docs.yml)
[![python](https://github.com/Azure/shrike/actions/workflows/python.yml/badge.svg)](https://github.com/Azure/shrike/actions/workflows/python.yml)
[![Component Governance](https://dev.azure.com/msdata/Vienna/_apis/build/status/aml-ds/Azure.shrike%20Component%20Governance?branchName=main)](https://dev.azure.com/msdata/Vienna/_build/latest?definitionId=16088&branchName=main)
[![ci-gate](https://dev.azure.com/msdata/Vienna/_apis/build/status/aml-ds/Azure.shrike%20ci-gate?branchName=main)](https://dev.azure.com/msdata/Vienna/_build/latest?definitionId=16115&branchName=main)
[![Python versions](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/Azure/shrike/branch/main/graph/badge.svg?token=sSq0BKlfTu)](https://codecov.io/gh/Azure/shrike)
[![license: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

Compliant Machine Learning is the practice of training, validating and deploying
machine learning models withou seeing the private data. It is needed in many
enterprises to satsify the strict compliance and privacy guarantees that 
they provide to their customers.

The library `shrike` is a set of Python utilities for compliant machine
learning, with a special emphasis on running pipeline in the platform of 
[Azure Machine Learning](https://github.com/Azure/azureml-examples). This
library mainly contains three components, that are

-  `shrike.confidential_logging`: utlities for confidential logging and 
exception handling;
-  `shrike.pipeline`: helper code for manging, validating and submitting Azure
Machine Learning pipelines based on 
[azure-ml-component](https://componentsdk.z22.web.core.windows.net/index.html);
-  `shrike.build`: helper code for packaging, building, validating, signing and
registering Azure Machine Learning components.

## Documentation
For the full documentation of `shrike` with detailed examples and API reference, 
please see the [docs page](http://azure.github.io/shrike).


## Installation
To install via PyPi, please type:
```pwsh
pip install shrike[pipeline,build]
```
There are three optional extra dependenciies - `pipeline`, `build` and `dev`, 
among which `dev` is for the development environment of shrike. 
If only the confidential-logging feature would be used, please 
just type without any extras:
```pwsh
pip install shrike
```

## Need Support?
When you have any feature requests or technical questions or find
any bugs, please don't hesitate to contact the Azure ML Data Science
Team.

- If you are Microsoft employees, please refer to the 
[support page](https://aka.ms/aml/support) for details;
- If you are outside Microsoft, feel free to send an email
to [aml-ds@microsoft.com](mailto:aml-ds@microsoft.com). 


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
