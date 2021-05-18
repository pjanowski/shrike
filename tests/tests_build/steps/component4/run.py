# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

    Author: Shize Su for Microsoft
    Contact: shizs@microsoft.com
"""
import os
import argparse
from subprocess import run as subprocess_run
from subprocess import PIPE, STDOUT, Popen
import subprocess
import shutil
import tempfile
import zipfile
from distutils.dir_util import copy_tree
from shrike.compliant_logging.constants import DataCategory
from shrike.compliant_logging.exceptions import prefix_stack_trace
from shrike.compliant_logging import enable_compliant_logging
import logging


def run_windows_command(one_command, log):
    try:
        log.info("command is " + one_command, category=DataCategory.PUBLIC)
        proc = subprocess_run(one_command, stdout=PIPE, stderr=STDOUT, check=True)
        log.info(proc.stdout.decode("utf-8"), category=DataCategory.PRIVATE)
    except subprocess.CalledProcessError as e:
        log.info(
            "We got error while running command. Error message is:",
            category=DataCategory.PUBLIC,
        )
        log.info(e.output.decode("utf-8"), category=DataCategory.PRIVATE)
        raise e


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", help="output directory", required=True)
    parser.add_argument(
        "--input_transcription_folder", help="input_transcription folder", required=True
    )
    parser.add_argument(
        "--input_transcription_filename",
        help="ex) input_text_script_audio_generate.txt",
        required=True,
    )
    parser.add_argument(
        "--input_transcription_phone_dict_filename",
        help="phone dict file name under input_transcription_folder ",
        required=True,
    )
    parser.add_argument("--InModelFold", help="input model folder ", required=True)
    parser.add_argument("--InSpeakName", type=str, default="02")
    parser.add_argument("--InTacotronStep", type=int, default=460000)

    return parser


def audio_generate_init(args, log):
    PythonEnv = tempfile.mkdtemp()
    # this path should be set in container image
    PythonEnv_zip = (
        "C:\\wkdir\\deps\\lib\\NeurallTTS_PythonEnvForTTSFeatures_compact.zip"
    )
    log.info("unzipping PythonEnv", category=DataCategory.PUBLIC)
    with zipfile.ZipFile(PythonEnv_zip, "r") as zip_ref:
        zip_ref.extractall(PythonEnv)
    log.info("PythonEnv is unzipped", category=DataCategory.PUBLIC)
    args.PythonEnv = PythonEnv

    Others_dir = tempfile.mkdtemp()
    # this path should be set in container image
    Others_zip = "C:\\wkdir\\deps\\lib\\others.zip"
    log.info("unzipping others", category=DataCategory.PUBLIC)
    with zipfile.ZipFile(Others_zip, "r") as zip_ref:
        zip_ref.extractall(Others_dir)
    log.info("others is unzipped", category=DataCategory.PUBLIC)

    log.info(
        "Copy some tools into the current working directory",
        category=DataCategory.PUBLIC,
    )

    shutil.copy(os.path.join(Others_dir, "others", "CheckPhoneSequences.exe"), ".")
    shutil.copy(os.path.join(Others_dir, "others", "GenerateSubFiles2.exe"), ".")
    copy_tree(os.path.join(Others_dir, "others", "0_Tools"), "0_Tools")


def audio_generate(args, log):
    PythonEnv = args.PythonEnv

    WorkDir = tempfile.mkdtemp()

    WorkDir1 = os.path.join(WorkDir, "1")
    OutPhoneSequencesFile = os.path.join(WorkDir, "1.1")
    log.info("Start text to phone sequence converting", category=DataCategory.PUBLIC)
    command1 = (
        "run_text_to_phone_sequences.cmd {WorkDir} {InTextScriptFile} {PythonEnv} {InSpeakName} {OutPhoneSequencesFile}"
    ).format(
        WorkDir=WorkDir1,
        InTextScriptFile=os.path.join(
            args.input_transcription_folder, args.input_transcription_filename
        ),
        PythonEnv=PythonEnv,
        InSpeakName=args.InSpeakName,
        OutPhoneSequencesFile=OutPhoneSequencesFile,
    )
    run_windows_command(command1, log)

    WorkDir2 = os.path.join(WorkDir, "2")
    OutPhoneSequencesScriptFile = os.path.join(WorkDir, "2.1")
    log.info("Check phone sequence", category=DataCategory.PUBLIC)
    command2 = (
        "run_check_phone_sequence.cmd {WorkDir} {InPhoneDictFile} {InPhoneSequencesFile} {OutPhoneSequencesScriptFile}"
    ).format(
        WorkDir=WorkDir2,
        InPhoneDictFile=os.path.join(
            args.input_transcription_folder,
            args.input_transcription_phone_dict_filename,
        ),
        InPhoneSequencesFile=OutPhoneSequencesFile,
        OutPhoneSequencesScriptFile=OutPhoneSequencesScriptFile,
    )
    run_windows_command(command2, log)

    WorkDir3 = os.path.join(WorkDir, "3")
    OutScriptFile0 = os.path.join(WorkDir, "output_script_0.txt")
    OutScriptFile1 = os.path.join(WorkDir, "output_script_1.txt")
    OutScriptFile2 = os.path.join(WorkDir, "output_script_2.txt")
    OutScriptFile3 = os.path.join(WorkDir, "output_script_3.txt")
    OutScriptFile4 = os.path.join(WorkDir, "output_script_4.txt")
    OutScriptFile5 = os.path.join(WorkDir, "output_script_5.txt")
    OutScriptFile6 = os.path.join(WorkDir, "output_script_6.txt")
    OutScriptFile7 = os.path.join(WorkDir, "output_script_7.txt")
    OutScriptFile8 = os.path.join(WorkDir, "output_script_8.txt")
    OutScriptFile9 = os.path.join(WorkDir, "output_script_9.txt")
    log.info("Generate subfiles for input", category=DataCategory.PUBLIC)
    command3 = "run_generate_sub_files_for_input.cmd {WorkDir} {InAllScriptFile} {OutScriptFile0} {OutScriptFile1} {OutScriptFile2} {OutScriptFile3} {OutScriptFile4} {OutScriptFile5} {OutScriptFile6} {OutScriptFile7} {OutScriptFile8} {OutScriptFile9}".format(
        WorkDir=WorkDir3,
        InAllScriptFile=OutPhoneSequencesScriptFile,
        OutScriptFile0=OutScriptFile0,
        OutScriptFile1=OutScriptFile1,
        OutScriptFile2=OutScriptFile2,
        OutScriptFile3=OutScriptFile3,
        OutScriptFile4=OutScriptFile4,
        OutScriptFile5=OutScriptFile5,
        OutScriptFile6=OutScriptFile6,
        OutScriptFile7=OutScriptFile7,
        OutScriptFile8=OutScriptFile8,
        OutScriptFile9=OutScriptFile9,
    )
    run_windows_command(command3, log)

    WorkDir4 = os.path.join(WorkDir, "4")
    OutMelsFile = os.path.join(WorkDir, "4.1")
    OutMelsFileAll = os.path.join(WorkDir, "4.2")
    if os.path.exists(OutMelsFileAll):
        shutil.rmtree(OutMelsFileAll)
    os.makedirs(OutMelsFileAll, exist_ok=True)
    log.info(
        "Start neural_tts_sample_generator module, text to phone sequence converting",
        category=DataCategory.PUBLIC,
    )
    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile0,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels001.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps001.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile1,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels002.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps002.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile2,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels003.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps003.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile3,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels004.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps004.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile4,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels005.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps005.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile5,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels006.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps006.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile6,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels007.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps007.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile7,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels008.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps008.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile8,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels009.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps009.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    command4 = (
        "run_neural_tts_sample_generator.cmd {WorkDir} {InPhoneSequencesFile} {PythonEnv} {InModelFold} {InTacotronStep} {OutMelsFile}"
    ).format(
        WorkDir=WorkDir4,
        InPhoneSequencesFile=OutScriptFile9,
        PythonEnv=PythonEnv,
        InModelFold=args.InModelFold,
        InTacotronStep=args.InTacotronStep,
        OutMelsFile=OutMelsFile,
    )
    run_windows_command(command4, log)
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.txt"),
        os.path.join(OutMelsFileAll, "mels010.txt"),
    )
    shutil.copy2(
        os.path.join(OutMelsFile, "mels.scp"),
        os.path.join(OutMelsFileAll, "scps010.scp"),
    )
    files = os.listdir(OutMelsFile)
    for f in files:
        os.remove(os.path.join(OutMelsFile, f))

    # Copy output mels data to output_dir
    if os.path.exists(args.output_dir):
        shutil.rmtree(args.output_dir)
    os.makedirs(args.output_dir, exist_ok=True)
    files = os.listdir(OutMelsFileAll)
    for f in files:
        shutil.move(os.path.join(OutMelsFileAll, f), args.output_dir)

    # shutil.move(OutMelsFile, args.output_dir)
    # shutil.move(WorkDir, args.output_dir)

    shutil.rmtree(WorkDir)


if __name__ == "__main__":
    enable_compliant_logging()
    log = logging.getLogger(__name__)
    log.info("job started", category=DataCategory.PUBLIC)

    parser = get_parser()

    args, unknowns = parser.parse_known_args()
    audio_generate_init(args, log)
    audio_generate(args, log)
    log.info("job finished", category=DataCategory.PUBLIC)
