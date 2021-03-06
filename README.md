# Packaging up a Snakemake workflow as a command-line tool

This repository shows how to package a Snakemake-based workflow as a
command-line tool.

Examples where this is used in practice:

* <https://github.com/NBISweden/minute>
* <https://github.com/NBISweden/IgDiscover/>

Instructions to the user would look like this, assuming the package is
named `workflowtool`

1. Install with `conda create -n workflowtool workflowtool`
   and activate the environment.
2. Run `workflowtool init pipelinedir` and change into the newly created
   directory `pipelinedir`.
3. Edit `workflowtool.yaml` and `samples.tsv`.
4. Run `workflowtool run`.


# Try it

The code in this repository works and can be installed and run:

1. Create and activate an environment with
   `virtualenv workflowtool && source workflowtool/bin/activate`
   (in reality, this would not use a Python virtualenv, but a Conda environment)
2. Run `pip install git+https://github.com/NBISweden/snakemake-workflow-tool`
3. Run `workflowtool init testdir`
4. `cd testdir`
5. Run `workflowtool run`

(We use a Python virtual environment for testing only. In practice, this would
need to be a Conda environment, see the next section.)


# Overview

## Conda package

The workflow looks like a regular Python package that can be installed with
`pip install`. Because `pip` can only install Python dependencies, which is
insufficient for workflows that use tools such as BWA, samtools etc., we never
advertise this way of installing and instead create a Conda package on Bioconda
that has a complete list of dependencies and then tell the user to use
`conda install` (or rather `conda create`)

(Note:
For IgDiscover, we even upload a package to PyPI (Python Package Index).
Installing this package with `pip install igdiscover` would be possible, but
it would probably fail as soon as the pipeline is run because of missing
dependencies. Having it on PyPI is somewhat convenient because the Conda recipe
can be written the same as other recipes that just re-package packages from
PyPI. Also, if a new release is made to PyPI, the Bioconda Bot detects this
and automatically opens a new PR with an updated Conda recipe.)

## The command-line tool

The Conda package installs a single command-line script `workflowtool` that has
typically at least two subcommands:

- `workflowtool init` creates a new "pipeline directory" and copies into it a
  configuration file template (which is read with `configfile:` in the
  Snakefile) and a sample sheet (such as `samples.tsv`). Both have enough
  comments and sane defaults so that the user understands how to adjust them.
- `workflowtool run` is mostly a wrapper around `snakemake` that adds some extra
  options, most importantly it provides the path to the Snakefile to be used
  (`-s .../path/to/Snakefile`) so that it is not necessary to have
  the Snakefile within the created pipeline directory. Any command-line
  arguments that it doesn???t understand are passed on to `snakemake` so that all
  the functionality is there.


## Layout of the Python package

These are the main files:
```
pyproject.toml
README.md
setup.cfg
src
????????? workflowtool
    ????????? cli
    ??????? ????????? __init__.py
    ??????? ????????? init.py
    ??????? ????????? run.py
    ????????? __init__.py
    ????????? __main__.py
    ????????? samples.tsv
    ????????? Snakefile
    ????????? workflowtool.yaml
```

### `pyproject.toml`

`pyproject.toml` marks this as a (modern) Python package. It specifies that
the "build backend" that we are using is `setuptools`.

### `setup.cfg`

`setup.cfg` contains the package???s metadata. It is used by setuptools.

* If you want to be compatible with Python 3.7, you need to depend on
  `importlib_metadata`.
* Because of the `workflowtool = workflowtool.__main__:main` setting,
  a command-line script named `workflowtool` will automatically be generated at
  installation time that invokes the `main()` function in the
  `workflowtool.__main__` module.


## How the `run` subcommand finds the `Snakefile`

The code for this is in `src/workflowtool/cli/run.py`.
The main point is to store the `Snakefile` *within the package directory*, so
in this case, `src/workflowtool/Snakefile`.
It can then be treated as "package data" and accessed with `importlib.resources`.
This looks roughly as follows:

```
with importlib.resources.path("workflowtool", "Snakefile") as snakefile:
    command = ["snakemake", "-p", "-s", snakefile]
    sys.exit(subprocess.call(command))
```

You will also need to ensure that the `Snakefile` is part of the `.tar.gz`
file by adding it to the `options.package_data` section in `setup.cfg`.


## The `init` command

The `workflowtool init` command also uses `importlib.resources` to obtain the
template configuration file and sample sheet. They are stored alongside
the Snakefile as package data (again, these need to be added to `setup.cfg`).
For example, this can be used to copy the configuration file into a newly
created pipeline directory:

```
configuration = importlib.resources.read_text("workflowtool", "workflowtool.yaml")
with open(Path(directory) / "workflowtool.yaml", "w") as f:
    f.write(configuration)
```
The code for the `init` subcommand is in `src/workflowtool/cli/init.py`.


## `__main__.py`

This contains the entry point for the command-line tool and sets up subcommands.

It autodetects which submodules exist in the `cli` module
(`init.py` and `run.py` in this case) and adds a subcommand for each one so
that it???s not necessary to manually maintain a list of subcommands.
Each of the subcommand/cli modules must have
- a docstring, which is used as the help text when the subcommand is
  invoked with `--help`,
- an `add_arguments()` function, which is called to set up command-line arguments,
- and a `main()` function, which is called when the subcommand is invoked.
