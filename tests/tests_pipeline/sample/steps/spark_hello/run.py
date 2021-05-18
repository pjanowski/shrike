# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import argparse
from argparse import ArgumentParser

import shrike
from shrike.compliant_logging.constants import DataCategory
from shrike.compliant_logging.exceptions import prefix_stack_trace
import logging
from pyspark.sql import SparkSession
import time


def parse_percentage(percentage) -> int:
    percentage = int(percentage)
    if percentage < 0 or percentage > 100:
        raise ArithmeticError(f"Percentage {percentage} < 0 or > 100")
    return percentage


def get_arg_parser(parser=None) -> ArgumentParser:
    rv = parser or argparse.ArgumentParser()

    rv.add_argument(
        "--input_path",
        required=True,
        type=str,
        help="Path to Heron extraction or other data to import from.",
    )

    rv.add_argument("--in_file_type", required=True, type=str, help="Input file type.")

    rv.add_argument(
        "--percent_take",
        required=True,
        type=parse_percentage,
        help="Integer percent of data to keep from this extraction.",
    )

    rv.add_argument(
        "--out_file_type", required=True, type=str, help="File type for output."
    )

    rv.add_argument(
        "--output_path",
        required=True,
        type=str,
        help="Path / filename to write the data extraction to.",
    )

    return rv


def get_spark_session(log: logging.Logger) -> SparkSession:
    start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    app_name = f"aml-ds-hdi-canary-{start_time}"
    log.info(f"application name: {app_name}", category=DataCategory.PUBLIC)

    rv = SparkSession.builder.appName(app_name).getOrCreate()
    return rv


def run(args, log):
    log.info(f"Running module with arguments {args}", category=DataCategory.PUBLIC)

    spark = get_spark_session(log)

    log.info(
        f"Reading {args.in_file_type} files from {args.input_path}",
        category=DataCategory.PUBLIC,
    )

    df = spark.read.format(args.in_file_type).load(args.input_path)
    log.info(f"Data schema: {df.columns}", category=DataCategory.PUBLIC)

    n_rows = df.count()
    log.info(f"Data has {n_rows} rows", category=DataCategory.PUBLIC)

    n_take = int(n_rows * args.percent_take / 100)
    log.info(f"Keeping {n_take} rows", category=DataCategory.PUBLIC)

    df = df.limit(n_take)

    log.info(
        f"Writing {args.out_file_type} output data to {args.output_path}",
        category=DataCategory.PUBLIC,
    )
    df.write.format(args.out_file_type).mode("overwrite").option("header", True).save(
        args.output_path
    )

    log.info("Finishing HDI probe", category=DataCategory.PUBLIC)


@prefix_stack_trace(keep_message=True, allow_list=["SystemExit"])
def main():
    parser = get_arg_parser()
    args, _ = parser.parse_known_args()

    log = logging.getLogger(__name__)

    run(args, log)


if __name__ == "__main__":
    shrike.compliant_loggine.enable_compliant_logging()
    main()
