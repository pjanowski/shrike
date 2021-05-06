# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
This runnable graph can be used to create and store an LSTM model
from existing train/valid encoded datasets and vocabulary.

This can store the model as a dataset with a name (ex: candidate number).
"""
# pylint: disable=no-member
# NOTE: because it raises 'dict' has no 'outputs' member in dsl.pipeline construction
import os
import sys
from dataclasses import dataclass
from typing import Optional

from azure.ml.component import dsl
from shrike.pipeline.pipeline_helper import AMLPipelineHelper

# NOTE: if you need to import from pipelines.*
SMARTCOMPOSE_ROOT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if SMARTCOMPOSE_ROOT_PATH not in sys.path:
    print(f"Adding to path: {SMARTCOMPOSE_ROOT_PATH}")
    sys.path.append(str(SMARTCOMPOSE_ROOT_PATH))


class MultiNodeTrainingPipeline(AMLPipelineHelper):
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
        class multinodetrainingexample:  # pylint: disable=invalid-name
            """Config object constructed as a dataclass.

            NOTE: the name of this class will be used as namespace in your config yaml file.
            See conf/reference/lstmtraining.yaml for an example.
            """

            # input datasets names (and versions if necessary)
            train_encoded_data: str = "dummy_data"
            train_encoded_data_version: Optional[str] = "latest"
            valid_encoded_data: str = "dummy_data"
            valid_encoded_data_version: Optional[str] = "latest"
            vocab_data: str = "dummy_data"
            vocab_data_version: Optional[str] = "latest"

            # parameters
            node_count: int = 4

        # return the dataclass itself
        # for helper class to construct config file
        return multinodetrainingexample

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
        lstm_trainer = self.module_load("MultiNodeTrainer")

        # Here you should create an instance of a pipeline function (using your custom config dataclass)
        @dsl.pipeline(
            name="Training LSTM model only",
            description="Training LSTM model only",
            default_datastore=config.compute.compliant_datastore,
        )
        def training_pipeline_function(train_encoded, valid_encoded, vocab):
            """Pipeline function for this graph.

            Args:
                train_encoded (FileDataset) : encoded training data
                valid_encoded (FileDataset) : encoded validation data
                vocab (FileDataset) : encoding vocabulary

            Returns:
                dict[str->PipelineOutputData]: a dictionary of your pipeline outputs
                    for instance to be consumed by other graphs
            """
            # general syntax:
            # module_instance = module_class(input=data, param=value)
            # or
            # subgraph_instance = subgraph_function(input=data, param=value)

            training_step = lstm_trainer(
                train_file=train_encoded,
                validation_file=valid_encoded,
                vocab_file=vocab,
            )
            # each module should be followed by this call
            # in enabled the helper class to fill-up all the settings for this module instance
            self.apply_recommended_runsettings(
                "MultiNodeTrainer",
                training_step,
                gpu=True,
                node_count=config.multinodetrainingexample.node_count,
                process_count_per_node=4,
            )

            # return {key: output}
            return {"lstm_model": training_step.outputs.output_dir}

        # finally return the function itself to be built by helper code
        return training_pipeline_function

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
        train_encoded = self.dataset_load(
            name=config.multinodetrainingexample.train_encoded_data,
            version=config.multinodetrainingexample.train_encoded_data_version,
        )
        valid_encoded = self.dataset_load(
            name=config.multinodetrainingexample.valid_encoded_data,
            version=config.multinodetrainingexample.valid_encoded_data_version,
        )
        vocab = self.dataset_load(
            name=config.multinodetrainingexample.vocab_data,
            version=config.multinodetrainingexample.vocab_data_version,
        )

        # when all inputs are obtained, we call the pipeline function
        experiment_pipeline = pipeline_function(train_encoded, valid_encoded, vocab)

        # and we return that function so that helper can run it.
        return experiment_pipeline


# NOTE: main block is necessary only if script is intended to be run from command line
if __name__ == "__main__":
    # calling the helper .main() function
    MultiNodeTrainingPipeline.main()
