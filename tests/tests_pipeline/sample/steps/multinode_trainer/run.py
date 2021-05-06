# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Empty script
"""
import os
import sys
import logging
import argparse


def get_arg_parser(parser=None):
    """Adds module arguments to a given argument parser (or creates one if none given).

    Args:
        parser (argparse.parser): the argument parser instance

    Returns:
        argparse.ArgumentParser: the argument parser with constructed arguments
    """
    if parser is None:
        parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--vocab_file",
        type=str,
        help="vocab directory path (vocab generated from the train set)",
        required=True,
    )
    parser.add_argument(
        "--train_file", type=str, help="input training file path", required=True
    )
    parser.add_argument(
        "--validation_file", type=str, help="input validation file path", required=True
    )
    parser.add_argument(
        "--output_dir", type=str, help="directory to output checkpoints and metrics to"
    )

    return parser


def run(args):
    """Module run function, this does the actual work

    Args:
        args (argparse.NameSpace): arguments as specified in get_arg_parser()
    """
    pass


def main(cli_args=None):
    """Main function

    Args:
        cli_args (List[Str]): to force parsing of specific arguments (ex: from unit tests)
    """
    parser = argparse.ArgumentParser(__doc__)

    get_arg_parser(parser)

    # screams an exception and sys.exit() if there's an error
    # sends a warning on logs if there's an unknown arg
    args, _ = parser.parse_known_args(cli_args)

    run(args)


if __name__ == "__main__":
    main()
