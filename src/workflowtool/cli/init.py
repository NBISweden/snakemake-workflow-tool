"""
Create and initialize a new pipeline directory
"""
import logging
import os
from pathlib import Path
import importlib.resources
from typing import Optional

from . import CommandLineError


logger = logging.getLogger(__name__)


def add_arguments(parser):
    parser.add_argument("directory", type=Path, help="New pipeline directory to create")


def main(args, arguments):
    if arguments:
        raise CommandLineError("These arguments are unknown: %s", arguments)
    run_init(**vars(args))


def run_init(directory: Path):
    if " " in str(directory):
        raise CommandLineError("The name of the pipeline directory must not contain spaces")

    try:
        directory.mkdir()
    except OSError as e:
        raise CommandLineError(e)

    configuration = importlib.resources.read_text("workflowtool", "workflowtool.yaml")
    with open(Path(directory) / "workflowtool.yaml", "w") as f:
        f.write(configuration)

    samplesheet = importlib.resources.read_text("workflowtool", "samples.tsv")
    with open(Path(directory) / "samples.tsv", "w") as f:
        f.write(samplesheet)

    logger.info("Pipeline directory %s created", directory)
    logger.info(
        'Edit %s/%s and run "cd %s && workflowtool run" to start the analysis',
        directory,
        "workflowtool.yaml",
        directory,
    )
