<h1 align="center">
  <img
    width="200"
    height="200"
    src="https://user-images.githubusercontent.com/11076525/165836171-9ffdea6e-1633-440c-be06-b46e1e3e4e04.png"
  >
  <br>
  Neighborly
</h1>

<h3 align="center"><b>Social simulation engine for procedurally generating towns of characters</b></h2>

<p align="center">
  <img src="https://img.shields.io/pypi/dm/neighborly">
  <img src="https://img.shields.io/pypi/l/neighborly">
  <img src="https://img.shields.io/pypi/v/neighborly">
  <img src="https://img.shields.io/pypi/pyversions/neighborly">
</p>

# Overview

Neighborly is a simulationist story generator inspired by
[_Talk of the Town_](https://www.jamesryan.world/projects#/talktown/). It combines an
agent-based social simulation with a
[storylet-style](https://emshort.blog/2019/11/29/storylets-you-want-them/) architecture
to create emergent narratives among the characters within its simulated town.
Neighborly simulates the lives of each character, their jobs, routines, and relationships.
Users can specify custom character types, businesses, occupations, and life events.
Neighborly is not designed to be a full experience, it is meant to be used as a
content generator tool that powers a more complete game.

# Core Features

* Create custom Character, Business, and Occupation types
* Use Plugins to create and share custom content
* Dynamically sequence events in character's lives
  (relationship milestones, job changes, victories, tragic events)
* Export simulation data to JSON

# How to use

Neighborly is available to install from PyPI.

```bash
pip install neighborly
```

## Using as a library

Neighborly can be used as a library within a Python script or package.
The `samples` directory contains python scripts that use Neighborly this
way. Please refer to them when creating new Plugins and other content.

## Running the CLI

Neighborly can be run as a module from the commandline.

```bash
python -m neighborly

# Please use the following command for additional help with running Neighborly's CLI
python -m neighborly --help
```

By default, it runs a builtin version of **Talk of the Town**. However, you can
configure the simulation settings by creating a `neighborlyconfig.yaml` file in
the same directory where you're running the CLI. Please refer to the
[wiki](https://github.com/ShiJbey/neighborly/wiki/Config-Files) for a list of
valid configuration settings.

When world generation concludes, Neighborly can write the final simulation data
to a JSON file with the name of the town and the seed used for random number
generation.

# Running the Samples

Neighborly provides sample simulations to show users how to customize
it to create new story world themes.

Please follow the steps below to run the sample simulations.
We also have examples for using Neighborly in a IPython
notebook and with PyGame.

```bash
# Make sure that you've activated your python virtual environment
#  created in "Installing For Local Development" Step-2

# Step 1: Install dependencies for samples
python -m pip install -e ".[samples]"

# Step 2: Run desired sample
#   Replace <sample_name>.py with the name of the
#   sample you want to run
python ./samples/<sample_name>.py

# (Optional: IPython Notebook)
# Step 3: Start Jupyter, navigate the sample.ipynb file,
#   and follow the instructions in the notebook
jupyter notebook
```

# Documentation

Most of Neighborly's documentation lives within the code. Neighborly uses
[Numpy-style](https://numpydoc.readthedocs.io/en/latest/format.html) docstrings for
functions and classes.

The extended documentation can be found in the
[Wiki](https://github.com/ShiJbey/neighborly/wiki).

When adding docstrings for existing or new bits of code please use the following
references for how to format your contributions. Please note that **Neighborly does
not use Sphinx** for documentation. We reference them here for the clear examples of
Numpy-style docstrings.

* [Sphinx Napoleon Plugin for processing Numpy Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
* [Example Numpy Style Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html#example-numpy)

# Contributing

If you are interested in contributing to Neighborly, feel free to fork this repository,
make your changes, and submit a pull-request. Please keep in mind that this project is
a tool for creativity and learning. We have a [code of conduct](./CODE_OF_CONDUCT.md)
to encourage healthy collaboration, and will enforce it if we need to.

Here are some ways that people can contribute to Neighborly:

1. Proposing/Implementing features
2. Fixing bugs
3. Providing optimizations
4. Fixing typos
5. Filing issues
6. Contributing tutorials/how-tos to the wiki
7. Fixing grammar and spelling
8. Creating new samples

## Installing for local development

If you wish to download a Neighborly for local development, follow the these instructions.

```bash
# Step 1: Clone Repository
git clone https://github.com/ShiJbey/neighborly.git

# (For Linux and MacOS)
# Step 2: Create and activate python virtual environment
cd neighborly
python3 -m venv venv
source ./venv/bin/activate

# (For Windows)
# Step 2: Create and activate python virtual environment
cd neighborly
python -m venv venv
./venv/Scripts/Activate

# Step 3: Install for local development
python -m pip install -e "."
```

## Code Style

Neighborly generally follows the [PEP-8 style guide](https://peps.python.org/pep-0008/).
However, code style is automatically handled by
[Black](https://black.readthedocs.io/en/stable/). Neighborly also uses
[isort](https://pycqa.github.io/isort/) for import storting.

You can follow
[these instructions](https://black.readthedocs.io/en/stable/integrations/editors.html)
to setup up both black and isort.

## Running the Tests

The tests are currently out-of-date and may refer to systems
and logic that no longer exists in Neighborly. The codebase
changes so frequently that it hasn't been worth the time.
As modules  become more established, I will add proper tests for them.
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

# Non-Deterministic Behavior

Neighborly aims to provide users with a deterministic pseudo-random simulation
experience. This means that users should observe the same behavior when providing
the simulation with the same configuration parameters. It does this to encourage
reproducibility of result when using Neighborly for research experimentation.

We try to remove all forms of non-determinism, but some slip through. The known
areas are listed below. If you find any, please make a new issue with details of
the behavior.

- **Names may not be consistent**: Names are generated using [Tracery](https://github.com/aparrish/pytracery).
We would need to create a custom version that uses an RNG instance instead of the
global random module to generate names.

# DMCA Statement

Upon receipt of a notice alleging copyright infringement, I will take whatever action it deems
appropriate within its sole discretion, including removal of the allegedly infringing materials.

The repo image is something fun that I made. I love _The Simpsons_, and I couldn't think of anything more neighborly
than Ned Flanders. If the copyright owner for _The Simpsons_ would like me to take it down,
please contact me.

The same takedown policy applies to any code samples inspired by TV shows, movies, and games.
