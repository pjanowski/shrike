# Creating an Azure DevOps Build for Signing and Registering

By reading through this doc, you will be able to

- have a high-level understanding of how to use `shrike.build`, and 
- create a **single-YAML** pipeline build in Azure DevOps for validating, signing and registering AML components.

## Requirements

To enjoy this tutorial, you need to 

-  have at least one [AML component YAML specification file](https://componentsdk.azurewebsites.net/components/command_component.html#how-to-write-commandcomponent-yaml-spec) in your team's repository,
-  have an [AML service connection](https://docs.microsoft.com/en-us/azure/devops/pipelines/library/service-endpoints?view=azure-devops&tabs=yaml) set up in your Azure DevOps for your Azure subscription,
-  have an [ESRP service connection](https://microsoft.sharepoint.com/teams/prss/esrp/info/ESRP%20Onboarding%20Wiki/ESRP%20Onboarding%20Guide%20Wiki.aspx) set up in your Azure DevOps, and
-  have a basic knowledge of Azure DevOps pipeline [YAML schema](https://docs.microsoft.com/en-us/azure/devops/pipelines/yaml-schema?view=azure-devops&tabs=schema%2Cparameter-schema).


## Configuration
Command line arguments and configuration YAML file are both supported by `shrike.build`. The order of precedence from least to greatest (the last listed variables override all other variables) is: default values, configuration file, command line arguments.

An example of configuration YAML file:
```yaml
# Choose from two signing mode: aml, or aether
signing_mode: aml

# Two methods are provided to find "active" components: all, or smart
# For "all" option, all the components will be validated/signed/registered
# For "smart" option, only those changed components will be processed.
activation_method: all

# Regular expression that a branch must satisfy in order for this code to
# sign or register components.
compliant_branch: ^refs/heads/main$

# Determine the working directory. Default: '.'
working_directory: '.'

# Glob path of all component specification files.
component_specification_glob: 'steps/**/module_spec.yaml'

log_format: '[%(name)s][%(levelname)s] - %(message)s'

# List of workspace ARM IDs
workspaces: 
- /subscriptions/48bbc269-ce89-4f6f-9a12-c6f91fcb772d/resourcegroups/aml1p-rg/providers/Microsoft.MachineLearningServices/workspaces/aml1p-ml-wus2
- /subscriptions/2dea9532-70d2-472d-8ebd-6f53149ad551/resourcegroups/MOP.HERON.PROD.aa8dad83-8884-48de-8b0e-3f3880e7386a/providers/Microsoft.MachineLearningServices/workspaces/amlworkspace4frmqmkryoyzc

# Boolean argument: What to do when the same version of a component has already been registered.
# Default: False
fail_if_version_exists: False

# Boolean argument: Will the build number be used or not
use_build_number: True
```

To consume this configuration file, we should pass its path to the command line, that is
```ps
python -m shrike.build.commands.prepare --configuration-file PATH/TO/MY_CONFIGURATION_FILE
```
If we want to override the values of `work_directory` and `fail_if_version_exists` at runtime, we should append them to the command line:
```ps
python -m shrike.build.commands.prepare --configuration-file PATH/TO/MY_CONFIGURATION_FILE --working-directory MY_ANOTHER_WORKDIRECTORY --fail-if-version-exists
```


### "Smart" mode

The `shrike` package supports a "smart" `activation_method`. Using this "smart" mode will only register the components that were modified. The logic used to identify which components are modified is as follows.

1. If a file located in the component folder is changed, then the component is considered to be modified.
2. If a file listed in the `additional_includes` file (file directly listed, or its parent folder listed) is changed, then the component is considered to be modified.

> Note: A corollary of point 2 above is that if you modify a function in a helper file listed in the `additional_includes`, your component will be considered as modified even if it does not use that function at all. That is why we use quotes around "smart": the logic is not smart enough to detect _only_ the components _truly_ affected by a change (implementing that logic would be a much more complicated task).  

> Note: Another corollary of point 2 is that if you want to use the "smart" mode, you need to be as accurate as possible with the files listed in the `additional_includes`, otherwise components might be registered even though the changes didn't really affect them. Imagine the extreme case where you have a huge `utils` directory listed in `additional_includes` instead of the specific list of utils files: every change to that directory, even if not relevant to your component of interest, will trigger the registration. This would defeat the purpose of having a smart mode in the first place.

It is worth reiterating that for the tool to work properly, **the name of the compliant branch in your config file should be of the form "`^refs/heads/<YourCompliantBranchName>$`"**. (Notice how it starts with "`^refs/heads/`" and ends with "`$`".)

To identify the latest merge into the compliant branch, the tool relies on the Azure DevOps convention that the commit message starts with "Merged PR". **If you customize the commit message, please make sure it still starts with "Merged PR", otherwise the "smart" logic will not work properly.**

## Preparation step
In this section, we briefly describe the workflow of the `prepare` command in the library `shrike`, that is

1. Search all AML components in the working directory by matching the glob path of component specification files,
2. Validate all "active" components,
3. Build all "active" components, and
4. Create files `catlog.json` and `catalog.json.sig` for each "active" component.

> Note: While building "active" components, all additional dependency files specified in `.additional_includes` will be copied into the component build folder by 
the `prepare` command. However, for those dependecy files that are not checked into the repository, such as Odinmal Jar (from NuGet packages) and .zip files, we need to write extra "tasks" to 
copy them into the component build folder.

A sample YAML script of preparation step

```yaml
- task: AzureCLI@2
  displayName: Preparation
  inputs:
    azureSubscription: $(MY_AML_WORKSPACE_SERVICE_CONNECTION)
    scriptLocation: inlineScript
    scriptType: pscore
    inlineScript: |
      python -m shrike.build.commands.prepare --configuration-file PATH/TO/MY_CONFIGURATION_FILE
    workingDirectory: $(MY_WORK_DIRECTORY)
```

## ESRP CodeSign
After creating `catlog.json` and `catalog.json.sig` files for each built component in the preparation step, we leverage the ESRP, that is *Engineer Sercurity and Release Platform*, to sign
the contents of components. In the sample yaml script below, we need to customize `ConnectedServiceName` and `FolderPath`. In `TEEGit` repo, the name of ESRP service connection for Torus tenant 
(​cdc5aeea-15c5-4db6-b079-fcadd2505dc2​) is `Substrate AI ESRP`. For other repos, if the service connection for ESRP has not been set up yet, please refer to the 
[ESRP CodeSign task Wiki](https://microsoft.sharepoint.com/teams/prss/esrp/info/ESRP%20Onboarding%20Wiki/Integrate%20the%20ESRP%20Scan%20Task%20into%20ADO.aspx) for detailed instructions.

```yaml
- task: EsrpCodeSigning@1
    displayName: ESRP CodeSigning
    inputs:
    ConnectedServiceName: $(MY_ESRP_SERVICE_CONNECTION)
    FolderPath: $(MY_WORK_DIRECTORY)
    Pattern: '*.sig'
    signConfigType: inlineSignParams
    inlineOperation: |
      [
        {
          "KeyCode": "CP-460703-Pgp",
          "OperationCode": "LinuxSign",
          "parameters": {},
          "toolName": "sign",
          "toolVersion": "1.0"
        }
      ]
    SessionTimeout: 20
    VerboseLogin: true
```

> Note: This step requires one-time authorization from the administrator of your ESRP service connection. Please contact your manager or tech lead for authorization questions.

## Component registration
The last step is to register all signed components in our AML workspaces. The `register` class in the `shrike` library implements the registration procedure by executing 
Azure CLI command `az ml component --create --file {component}`. The Python call is

```python
python -m shrike.build.commands.register --configuration-file path/to/config
```
In this step, the `register` class can detect signed and built components
There are five configuration parameters related with registration step: `--compliant-branch`, `--source-branch`, `--fail-if-version-exists`, `--use-build-number`, and `--all-component-version`. We should customize them in the `configure-file` according to use cases.

- The `register` class checks whether the value of `source_branch` matches that of `compliant_branch` before starting registration. If their pattern doesn't match, an error message will be logged and the registraion step will be terminated.
- If `fail_if_version_exists` is True, an error is raised and the registration step is terminated when the version number of some signed component already exists in the workspace; Otherwise, only a warning is raised and the registration step continues.
- If `all_component_version` is not `None`, the value of `all_component_version` is used as the version number for all signed components.
- If `use_build_number` is True, the build number is used as the version number for all signed components (Overriding the value of `all_component_version` if `all_component_version` is not `None`).

A sample YAML task for registration is 
```yaml
- task: AzureCLI@2
    displayName: AML Component Registration
    inputs:
    azureSubscription: $(MY_AML_WORKSPACE_SERVICE_CONNECTION)
    scriptLocation: inlineScript
    scriptType: pscore
    inlineScript: |
      python -m shrike.build.commands.register --configuration-file PATH/TO/MY_CONFIGURATION_FILE
    workingDirectory: $(MY_WORK_DIRECTORY)
```

> Note: The `shrike` library is version-aware. For a component of product-ready version number (e.g., a.b.c), it is set as the default version in the registration step; 
Otherwise, for a component of non-product-ready version number (e.g., a.b.c-alpha), it will not be labelled as default. 

## Handling components which use binaries

For some components (e.g., Linux/Windows components running .NET Core DLLs or Windows Exes, or HDI components leveraging the ODIN-ML JAR or Spark .NET), the signed snapshot needs to contain some binaries. As long as **those binaries are compiled from human-reviewed source code or come from internal (authenticated) feeds**, this is fine. Teams may inject essentially arbitrary logic into their Azure DevOps pipeline, either for compiling C\# code, or downloading \& extracting NuGets from the Polymer NuGet feed.

## &AElig;ther-style code signing

This tool also assists with &AElig;ther-style code signing. Just write a configuration file like:

```yaml
component_specification_glob: '**/ModuleAutoApprovalManifest.json'
signing_mode: aether
```

and then run a code signing step like this just after the "prepare" command. Note: your ESRP service connection will need to have access to the `CP-230012` key, otherwise you'll encounter the error described in:

> [Got unauthorized to access CP-230012 when calling Aether-style signing service](https://stackoverflow.microsoft.com/a/256540/)

```yaml
- task: EsrpCodeSigning@1
  displayName: sign modules
  inputs:
    ConnectedServiceName: $(MY_ESRP_SERVICE_CONNECTION)
    FolderPath: $(MY_WORK_DIRECTORY)
    Pattern: '*.cat'
    signConfigType: inlineSignParams
    inlineOperation: |
      [
        {
          "keyCode": "CP-230012",
          "operationSetCode": "SigntoolSign",
          "parameters": [
              {
                "parameterName": "OpusName",
                "parameterValue": "Microsoft"
              },
              {
                "parameterName": "OpusInfo",
                "parameterValue": "http://www.microsoft.com"
              },
              {
                "parameterName": "PageHash",
                "parameterValue": "/NPH"
              },
              {
                "parameterName": "FileDigest",
                "parameterValue": "/fd sha256"
              },
              {
                "parameterName": "TimeStamp",
                "parameterValue": "/tr \"http://rfc3161.gtm.corp.microsoft.com/TSS/HttpTspServer\" /td sha256"
              }
          ],
          "toolName": "signtool.exe",
          "toolVersion": "6.2.9304.0"
        }
      ]
    SessionTimeout: 20
    VerboseLogin: true
```

&AElig;ther does not support "true" CI/CD, but you will be able to use your build drops to register compliant &AElig;ther modules following [Signed Builds](https://dev.azure.com/msdata/Vienna/_git/aml-ds?path=%2Fdocs%2FAether-for-compliant-experimentation%2FSigned-Builds.md&_a=preview).

For reference, you may imitate [this build used by the AML Data Science team](https://dev.azure.com/msdata/Vienna/_git/aml-ds?path=%2Frecipes%2Fsigned-components%2Fazure-pipelines.yml&version=GBmain&line=118&lineEnd=197&lineStartColumn=1&lineEndColumn=37&lineStyle=plain&_a=contents).

_Note:_ there is no need to run the AML-style and &AElig;ther-style code signing in separate jobs. So long as they both run in a Windows VM, it may be the same job.

