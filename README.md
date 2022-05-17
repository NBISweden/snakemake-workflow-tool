# Packaging up a Snakemake workflow as a command-line tool

Examples:

* <https://github.com/NBISweden/minute>
* <https://github.com/NBISweden/IgDiscover/>

Instructions to the user would look like this, assuming the workflow/tool is
named `myworkflow`

1. Install with `conda create -n myworkflow myworkflow`
   and activate the environment.
2. Run `myworkflow init pipelinedir` and change into the newly created directory
   `pipelinedir`.
3. Edit `myworkflow.yaml` and `samples.tsv`.
4. Run `myworkflow run`.


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

The Conda package installs a single command-line script `myworkflow` that has
typically at least two subcommands:

- `myworkflow init` creates a new "pipeline directory" and copies into it a
  configuration file template (which is read with `configfile:` in the
  Snakefile) and a sample sheet (such as `samples.tsv`). Both have enough
  comments and sane defaults so that the user understands how to adjust them.
- `myworkflow run` is mostly a wrapper around `snakemake` that adds some extra
  options, most importantly it provides the path to the Snakefile to be used
  (`-s .../path/to/Snakefile`) so that it is not necessary to have
  the Snakefile within the created pipeline directory. Any command-line
  arguments that it doesn’t understand are passed on to `snakemake` so that all
  the functionality is there.


## Layout of the Python package

In addition to `LICENSE` and `README.md`, these are the main files:

* `pyproject.toml`
* `setup.cfg`
* `src/myworkflow/__init__.py`
* `src/myworkflow/myworkflow.yaml`
* `src/myworkflow/Snakefile`
* `src/myworkflow/cli/__main__.py`
* `src/myworkflow/cli/init.py`
* `src/myworkflow/cli/run.py`

### `pyproject.toml`

`pyproject.toml` marks this as a (modern) Python package. It specifies that
the "build backend" that we are using is `setuptools`:

```
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
```

### `setup.cfg`

`setup.cfg` contains the package’s metadata.

```
[metadata]
name = myworkflow
author = The authors
author_email =
url = https://github.com/NBISweden/myworkflow/
description = Workflow for the analysis of data
license = MIT
version = 0.1.0
long_description = file: README.md
long_description_content_type = text/markdown
classifiers =
    Development Status :: 4 - Beta
    License :: OSI Approved :: MIT License
    Programming Language :: Python :: 3

[options]
python_requires = >=3.7
packages = find:
install_requires =
    importlib_metadata; python_version<'3.8'

[options.entry_points]
console_scripts =
    myworkflowwrappername = myworkflow.__main__:main

[options.package_data]
* =
    Snakefile
    multiqc_config.yaml
    myworkflow.yaml
```

* Remove the `importlib_metadata` dependency if you are on Python 3.8 or later
* Because of the `myworkflowwrappername = ...` setting, a command-line script
  will automatically be generated at installation time that invokes `main()`
  in the `myworkflow.__main__` module.

## How the `run` subcommand finds the `Snakefile`

The code for this is in `src/myworkflow/cli/run.py`.
The main point is to store the `Snakefile` *within the package directory*, so
in this case, `src/myworkflow/Snakefile`.
It can then be treated as "package data" and accessed with `importlib.resources`.
This looks roughly as follows:

```
with importlib.resources.path("myworkflow", "Snakefile") as snakefile:
    command = ["snakemake", "-p", "-s", snakefile]
    sys.exit(subprocess.call(command))
```

You will also need to ensure that the `Snakefile` is part of the `.tar.gz`
file by adding it to the `options.package_data` section in `setup.cfg`
(see above).


## The `init` command

The `myworkflow init` command also uses `importlib.resources` to obtain the
template configuration file and sample sheet. They are stored alongside
the Snakefile as package data (again, these need to be added to `setup.cfg`).
For example, this can be used to copy the configuration file into a newly
created pipeline directory:

```
configuration = importlib.resources.read_text("myworkflow", "myworkflow.yaml")
with open(Path(directory) / "myworkflow.yaml", "w") as f:
    f.write(configuration)
```
The code for the `init` subcommand would be in `src/myworkflow/cli/init.py`.


## Other files

* `src/myworkflow/__init__.py`
* `src/myworkflow/cli/__main__.py`
* `src/myworkflow/cli/init.py`
