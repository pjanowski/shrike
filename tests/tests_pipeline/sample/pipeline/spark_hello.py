# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Hello world example for Spark
"""
# pylint: disable=no-member
# NOTE: because it raises 'dict' has no 'outputs' member in dsl.pipeline construction
import os
import sys
from dataclasses import dataclass
from typing import Optional

from azure.ml.component import dsl
from shrike.pipeline.pipeline_helper import AMLPipelineHelper


class SparkHelloPipeline(AMLPipelineHelper):
    """Runnable/reusable pipeline helper class

    This class inherits from AMLPipelineHelper which provides
    helper functions to create reusable production pipelines for SmartCompose.
    """

    @classmethod
    def get_config_class(cls):
        """Returns the config object (dataclass) for this runnable script.

        Returns:
            dataclass: class for configuring this runnable pipeline.
        """

        @dataclass
        class sparkhelloworld:  # pylint: disable=invalid-name
            """Config object constructed as a dataclass.

            NOTE: the name of this class will be used as namespace in your config yaml file.
            See conf/reference/evaluate_qas_model.yaml for an example.
            """

            # input datasets names (and versions if necessary)
            input_dataset: str = "dummy_dataset"
            input_dataset_version: Optional[str] = "latest"

        # return the dataclass itself
        # for helper class to construct config file
        return sparkhelloworld

    def build(self, config):
        """Builds a pipeline function for this pipeline using AzureML SDK (dsl.pipeline).

        This method should build your graph using the provided config object.
        Your pipeline config will be under config.CONFIGNAME.*
        where CONFIGNAME is the name of the dataclass returned by get_config_class()

        This method returns a constructed pipeline function (decorated with @dsl.pipeline).

        Args:
            config (DictConfig): configuration object (see get_config_class())

        Returns:
            dsl.pipeline: the function to create your pipeline
        """
        # helper function below loads the module from registered or local version
        # depending on your config run.use_local
        spark_hello_component = self.module_load("SparkHelloWorld")

        # Here you should create an instance of a pipeline function (using your custom config dataclass)
        @dsl.pipeline(
            name="Spark Hello World Pipeline (Name)",
            description="Spark Hello World Pipeline (Description)",
            default_datastore=config.compute.compliant_datastore,
        )
        def baseline_pipeline_function(curatedemailreplypairs_dataset):
            """Pipeline function for this graph.

            Args:
                curatedemailreplypairs_dataset (TabularDataset) : the input eyes-on/eyes-off dataset provided as parquet files

            Returns:
                dict[str->PipelineOutputData]: a dictionary of your pipeline outputs
                    for instance to be consumed by other graphs
            """
            # general syntax:
            # module_instance = module_class(input=data, param=value)
            # or
            # subgraph_instance = subgraph_function(input=data, param=value)

            spark_hello_step = spark_hello_component(
                input_path=curatedemailreplypairs_dataset,
                in_file_type="parquet",
                percent_take=42,
                out_file_type="json",
            )
            # each module should be followed by this call
            # in enabled the helper class to fill-up all the settings for this module instance
            self.apply_recommended_runsettings("SparkHelloWorld", spark_hello_step)
            # return {key: output}
            return spark_hello_step.outputs

        # finally return the function itself to be built by helper code
        return baseline_pipeline_function

    def pipeline_instance(self, pipeline_function, config):
        """Given a pipeline function, creates a runnable instance based on provided config.

        This is used only when calling this as a runnable pipeline using .main() function (see below).
        The goal of this function is to map the config to the pipeline_function inputs and params.

        Args:
            pipeline_function (function): the pipeline function obtained from self.build()
            config (DictConfig): configuration object (see get_config_class())

        Returns:
            azureml.core.Pipeline: the instance constructed with its inputs and params.
        """
        # NOTE: self.dataset_load() helps to load the dataset based on its name and version
        pipeline_input_dataset = self.dataset_load(
            name=config.sparkhelloworld.input_dataset,
            version=config.sparkhelloworld.input_dataset_version,
        )

        # when all inputs are obtained, we call the pipeline function
        experiment_pipeline = pipeline_function(pipeline_input_dataset)

        # and we return that function so that helper can run it.
        return experiment_pipeline


# NOTE: main block is necessary only if script is intended to be run from command line
if __name__ == "__main__":
    # calling the helper .main() function
    SparkHelloPipeline.main()
