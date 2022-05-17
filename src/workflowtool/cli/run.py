"""
Run the pipeline

Some more explanation of what the run command does

Calls Snakemake to produce all the output files.

Any arguments that this wrapper script does not recognize are forwarded to Snakemake.
This can be used to provide file(s) to create, targets to run or any other Snakemake
options.

Run 'snakemake --help' or see the Snakemake documentation to see valid snakemake arguments.
"""
import importlib
import logging
import subprocess
import sys
from pathlib import Path
from ruamel.yaml import YAML


logger = logging.getLogger(__name__)


def add_arguments(parser):
    parser.add_argument(
        "--cores",
        "-c",
        metavar="N",
        type=int,
        help="Run on at most N CPU cores in parallel. Default: Use as many cores as available)",
    )


def main(args, arguments):
    run_snakemake(**vars(args), arguments=arguments)


def run_snakemake(
    cores=None,
    arguments=None,
):
    try:
        _ = YAML(typ="safe").load(Path("workflowtool.yaml"))
    except FileNotFoundError as e:
        sys.exit(
            f"Pipeline configuration file '{e.filename}' not found. "
            f"Please see the documentation for how to create it."
        )

    with importlib.resources.path("workflowtool", "Snakefile") as snakefile:
        command = [
            "snakemake", f"--cores={'all' if cores is None else cores}", "-p", "-s", snakefile
        ]
        if arguments:
            command += arguments
        logger.debug("Running: %s", " ".join(str(c) for c in command))
        exit_code = subprocess.call(command)

    sys.exit(exit_code)
