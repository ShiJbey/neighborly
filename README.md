<h1 align="center">
  <img
    width="150"
    height="150"
    src="https://user-images.githubusercontent.com/11076525/165836171-9ffdea6e-1633-440c-be06-b46e1e3e4e04.png"
  >
  <br>
  Neighborly (v0.10.0)
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/status-unstable-critical?style=flat">
  <img src="https://img.shields.io/pypi/v/neighborly">
  <img src="https://img.shields.io/pypi/pyversions/neighborly">
  <img src="https://img.shields.io/pypi/l/neighborly">
  <img src="https://img.shields.io/pypi/dm/neighborly">
  <img src="https://img.shields.io/badge/code%20style-black-black">
  <img src="https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336">
</p>

# Overview

Neighborly is a Python framework for generating and forward simulating towns of
characters over large periods of time (decades to centuries). It uses a character-driven
social simulation that forward-simulates the lives of each character, their jobs,
routines, relationships, and life events. Users can specify custom characters,
residential/commercial buildings, occupations, life events, social actions, and more.

Currently, _Neighborly_ works best as narrative data generator. When the simulation
ends, users can save the history of events, characters, relationships, and other stuff.

Neighborly was inspired by lessons learned from working with
[_Talk of the Town_](https://github.com/james-owen-ryan/talktown)
and aims to give people better documentation, simpler interfaces, and more opportunities
for extension and content authoring.

## Core Features

- Create custom character, buildings, life events, and social actions
- Commandline interface (CLI) tool
- Configure the CLI using YAML text files
- Plugin architecture allows users to modularize and share their custom content
- Export simulation state to JSON for further data processing

# How to use

Below are instructions for installing Neighborly and the options one has for using it
in their projects. If you want examples of how to use Neighborly and how to extend it
with custom content, please refer to
[Neighborly's wiki](https://github.com/ShiJbey/neighborly/wiki) and the sample scripts
in the [_samples_ directory](https://github.com/ShiJbey/neighborly/tree/main/samples).

## Installation

Neighborly is available to install from PyPI.

```bash
pip install neighborly
```

Or you can install it by cloning the main branch of this repo and installing that.

```bash
git clone https://github.com/ShiJbey/neighborly.git

cd neighborly

python -m pip install .
```

## Using as a library

Neighborly can be used as a library within a Python script or package.
The `samples` directory contains python scripts that use Neighborly this
way. Please refer to them when creating new Plugins and other content.

## Running the CLI

Neighborly can be run as a module `$ python -m neighborly` or commandline `$ neighborly`
script. If you require additional help while running, please use
`python -m neighborly --help` or `neighborly --help`.

By default, Neighborly runs a builtin version of **Talk of the Town**. However, you can
configure the simulation settings by creating a `neighborlyconfig.yaml` file in
the same directory where you're running the CLI. Please refer to the
[wiki](https://github.com/ShiJbey/neighborly/wiki/Neighborly-CLI) for a list of
valid configuration settings.

When world generation concludes, Neighborly can write the final simulation data
to a JSON file with the name of the town and the seed used for random number
generation.

## Running the Samples

Neighborly provides sample simulations to show users how to customize
it to create new story world themes.

```bash
# Make sure that you've activated your python virtual environment
# Replace <sample_name>.py with the name of the
# sample you want to run
python ./samples/<sample_name>.py
```

## Installing for local development

If you wish to download a Neighborly for local development, you need to clone/fork this
repository and install using the _editable_ flag (-e). Please see the instructions
below.

```bash
# Step One: Clone Repository
git clone https://github.com/ShiJbey/neighborly.git

# Step Two (Optional): Create and activate python virtual environment
cd neighborly

# For Linux and MacOS
python3 -m venv venv
source ./venv/bin/activate

# For Windows
python -m venv venv
./venv/Scripts/Activate

# Step Three: Install local build and dependencies
python -m pip install -e "."
```

## Running the Tests

The tests are currently out-of-date and may refer to systems
and logic that no longer exists in Neighborly. The codebase
changes so frequently that it hasn't been worth the time.
As modules become more established, I will add proper tests for them.
Feel free to contribute tests by forking the repo, adding your test(s), and
submitting a pull request with a description of your test cases. Your commits
should only contain changes to files within the `tests` directory. If you
change any files in other parts of the project, your PR will be rejected.

Please follow the steps below to run Neighborly's test suite. Neighborly uses
[PyTest](https://docs.pytest.org/en/7.1.x/) to handle unit testing.

```bash
# Step 1: Install dependencies for tests
python -m pip install -e ".[tests]"

# Step 2: Run Pytest
pytest

# Step3 : (Optional) Generate a test coverage report
pytest --cov=neighborly tests/
```

# Documentation

Neighborly uses [Numpy-style](https://numpydoc.readthedocs.io/en/latest/format.html)
docstrings in code and full documentation can be found in the
[Wiki](https://github.com/ShiJbey/neighborly/wiki).

When adding docstrings for existing or new bits of code please use the following
references for how to format your contributions:

- [Sphinx Napoleon Plugin for processing Numpy Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
- [Example Numpy Style Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html#example-numpy)

# Contributing

Here are some ways that people can contribute to Neighborly:

1. Proposing/Implementing new features
2. Fixing bugs
3. Providing optimizations
4. Fixing typos
5. Filing issues
6. Contributing tutorials/how-tos to the wiki
7. Fixing grammar and spelling in the wiki
8. Creating new samples/plugins

If you are interested in contributing to Neighborly, there are multiple ways to get
involved, and not all of them require you to be proficient with GitHub. Interested
parties can contribute to the core code base of Neighborly and/or create nre content
in the way of plugins. I love feedback, and if you have any questions, create a new
issue, and I will do my best to answer. If you want to contribute to the core code,
free to fork this repository, make your changes, and submit a pull-request with a
description of your contribution. Please keep in mind that this project is a
tool for creativity and learning. I have a [code of conduct](./CODE_OF_CONDUCT.md) to
encourage healthy collaboration, and will enforce it if I need to.

## Code Style

Neighborly uses [_Black_](https://black.readthedocs.io/en/stable/) to handle code style
and sorts imports using [_isort_](https://pycqa.github.io/isort/). You can follow
[these instructions](https://black.readthedocs.io/en/stable/integrations/editors.html)
for setting up both black and isort.

# Notes

## Non-Deterministic Behavior

The goal of having a seeded pseudo random simulation is so that users experience
deterministic behavior when using the same starting seed. I try to remove all forms of
non-determinism, but some slip through. The known areas are listed below. If you find
any, please make a new issue with details of the behavior.

- Neighborly uses [Tracery](https://github.com/aparrish/pytracery) to generate names for
  characters and locations, and these names may not be consistent despite using the same
  rng seed value.

## DMCA Statement

Upon receipt of a notice alleging copyright infringement, I will take whatever action it
deems appropriate within its sole discretion, including removal of the allegedly
infringing materials.

The repo image is something fun that I made. I love _The Simpsons_, and I couldn't think
of anyone more neighborly than Ned Flanders. If the copyright owner for _The Simpsons_
would like me to take it down, please contact me. The same takedown policy applies to
any code samples inspired by TV shows, movies, and games.
