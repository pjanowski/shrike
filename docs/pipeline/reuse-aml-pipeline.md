# General process for reusing and configuring an existing AML experiment

## Motivations

Essentially, an AML experiment is made of:
- a runnable python script,
- a configuration file.

They are checked in a repository, making it reusable and shareable in your team. In many cases, it will be easy to copy an existing experiment to make it your own by just modifying the configuration file. In some instances, you'll want to modify the python script as well to have a more in-depth change on the structure of the graph.

## 1. Branch from an existing experiment

In this section, we'll assume you have identified an existing runnable script (ex: `baseline.py`) and a configuration file (ex: `conf/reference/baseline.yaml`)
1. Create a new branch in your team's repository (to avoid conflicts).

2. In the `conf/reference/` or `conf/experiments/` folders, identify a config file you want to start from.

3. Copy this file into a new configuration file of your own.

4. If this configuration file has a module manifest specified in the defaults section, as an example:

    ```yaml
    defaults:
      - aml: eyesoff
      - compute: eyesoff
      - modules: baseline # list of modules + versions, see conf/modules/
    ```

    Copy the file under `conf/modules/baseline.yaml` to a file of your own (ex: `baseline-modelX.yaml`), and rename the name under `defaults` in your experiment config accordingly.

    ```yaml
    defaults:
      - aml: eyesoff
      - compute: eyesoff
      - modules: baseline-modelX # <<< modify here
    ```

    In the following sections, you will be able to pin each module in this manifest to a particular version number, different from your colleagues version numbers.

4. In the `run` section, modify your experiment name:

    ```yaml
    run: # params for running pipeline
      experiment_name: "modelX" # <<< modify here
    ```

    > Note: we recommend to use a different experiment for each project you work on. Experiments are essentially just a folder to put all your runs in order.

5. That's it, at this point we invite you to try running the script for validating the graph (see below as an example):

    ```powershell
    python pipelines/reference/baseline.py --config-dir ./conf --config-name experiments/modelX
    ```

    This will try to build the graph, but will not submit it as an experiment. You're ready to modify the experiment now.

# 2. Modifying the code (best practices)

Here's a couple recommendations depending on what you want to do.

## Your experiment consists in modifying modules only

If your experiment consists in modifying one or several modules only (not the structure of the graph).

- work in a branch containing your module code
- use local code to experiment
- create a specific configuration file for your experiment that shows which module versions to use
- when satisfied, merge in to main/master and register the new versions for your team to share.

## Your experiment consists in modifying the graph structure

- work in a branch containing your graph
- identify conflicts of versions with your team and either create a new graph or modify the existing one with options to switch on/off your changes
- create a specific configuration file for your experiment that shows which module versions to use
- when satisfied, merge in to main/master so that the team can reuse the new graph

# 3. Experiment with local code

If you want to modify a particular module for your experiment, we recommend to iterate on the module code using detonation chamber.

**IMPORTANT**: this is NOT possible for HDI modules. If you want to modify HDI modules, we recommend to test those first in eyes-on, or to register new versions of those HDI modules in parallel of your experiment branch (create a specific branch for your new module versions).

To use the local code for a given module:

## Identify the module key

Identify the module **key**, this is the key used to map to the module in the graphs/subgraphs code.

1. Go to the graph or subgraph you want to modify, check in the `build()` function to identify the module load key used. For instance below we want to modify `VocabGenerator`:

    ```python
    def build(self, config):
        # ...
        vocab_generator = self.module_load("VocabGenerator")
        # ...
    ```

2. If your pipeline uses the `required_modules()` method, this key will match with an entry in the required modules dictionary:

    ```python
    @classmethod
    def required_modules(cls):
        return {
            "VocabGenerator":{
                # references of remote module
                "remote_module_name":"SparkVocabGenerator", "namespace":"microsoft.com/office/smartcompose", "version":None,
                # references of local module
                "yaml_spec":"spark_vocab_generator/module_spec.yaml"
            },
    ```

    The key here is `VocabGenerator`, which is not the module name, but its key in the required modules dictionary.

3. If your pipeline uses a module manifest in yaml (recommended!), this key will map to an entry in the modules manifest file `conf/modules/baseline-modelX.yaml`:

    ```yaml
    manifest:
      # ...
      - key: "VocabGenerator"
        name: "microsoft.com/office/smartcompose://SparkVocabGenerator"
        version: null
        yaml: "spark_vocab_generator/module_spec.yaml"
      # ...
    ```

    The key here is `VocabGenerator`, which is not the module name, but its key in the required modules dictionary.

    > Note: if no `key` is specified, the `name` is used as key.

## Use module key to run this module locally

1. Use the `use_local` command with that key. You can either add it to the command line:

    ```powershell
    python pipelines/reference/baseline.py --config-dir ./conf --config-name experiments/modelX module_loader.use_local="VocabGenerator"
    ```

    Or you can write it in your configuration file:
    ```yaml
    # module_loader 
    module_loader: # module loading params
      # IMPORTANT: if you want to modify a given module, add its key here
      # see the code for identifying the module key
      # use comma separation in this string to use multiple local modules
      use_local: "VocabGenerator"
    ```

2. When running the experiment, watch-out in the logs for a line that will indicate this module has loaded from local code:

    ```
    Building subgraph [Encoding as EncodingHdiPipeline]...
    --- Building module from local code at spark_vocab_generator/module_spec.yaml
    ```

# 4. Experiment with different versions of (registered) modules

The way the helper code decides which version to use for a given module M is (in order):

- if `module_loader.force_all_module_version` is set, use it as version for module M (and all others)
- if a version is set under module M in `modules.manifest`, use it
- if a version is hardcoded in `required_modules()` for module M, use it
- if `module_loader.force_default_module_version` is set, use it as version for module M (and all others non specified versions)
- else, use default version registered in AML (usually, the latest).

Version management for your experiment modules can have multiple use cases.

## Use a specific version for all unspecified (`force_default_module_version`)

If all your modules versions are synchronized in the registration build, you can use this to use a single version number accross all the graph for all modules that have unspecified versions (`version:null`). If you want to pin down a specific version number outside of this, you can add a specific version in your module manifest, or in the `required_modules()` method.

## Use a specific version for all modules

If all your modules versions are synchronized in the registration build, you can use this to use a single version number accross all the graph for all modules. This will give you an exact replication of the modules at a particular point in time. This will override all other version settings.

## Use specific versions for some modules

If you want to pin down a specific version number for some particular modules, specify this version in the module manifest:

```yaml
# @package _group_
manifest:
  # ...
  - key: "LMPytorchTrainer"
    name: "[SC] [AML] PyTorch LM Trainer"
    version: null # <<< HERE
    yaml: "pytorch_trainer/module_spec.yaml"
  # ...
```

or hardcode it (not recommended) in your `required_modules()` method:

```python
   @classmethod
    def required_modules(cls):
        return {
            "LMPytorchTrainer":{
                "remote_module_name":"[SC] [AML] PyTorch LM Trainer",
                "namespace":"microsoft.com/office/smartcompose",
                "version":None, # <<< HERE
                "yaml_spec":"pytorch_trainer/module_spec.yaml"
            }
        }
```
