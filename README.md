<h1 align="center">
  <img
    width="300"
    height="300"
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

Neighborly is a social simulation engine for procedurally generating towns of characters. It simulates
the lives of each character, their jobs, routines, relationships, and life events. Neighborly utilizes
an entity-component system architecture, and enables users to specify custom character types, businesses,
occupations, and life events.

Neighborly takes lessons learned from working with
[_Talk of the Town_](https://github.com/james-owen-ryan/talktown)
and aims to give people better documentation, simpler interfaces, and more opportunities for extension and content authoring.

# Core Features

* Create custom Character Archetypes and have them all interact within the same simulation
* Create custom Business and Occupation definitions
* Configure simulation data using YAML or in code with Python
* Plugin architecture allows users to modularize and share their custom content
* Low fidelity simulation simulates the macro events in character's lives (relationship milestones, job changes, victories, tragic events)
* Export simulation state to JSON for further data processing

# Tutorials and How-to Guides

I plan to add these after I have finished implementing Neighborly's core
functionality. I will try to align them with the sample projects, but we
will see how the first pre-release looks. For now, loosely refer to the
samples. Although, they too lag behind breaking changes to the core codebase.

# Installing from PyPI

Neighborly is available to install via pip.

```bash
pip install neighborly
```

# Running the commandline tool

Neighborly can be run as a module from the commandline. By default, it runs a
builtin version of **Talk of the Town**. You can configure the simulation settings
by creating a `neighborlyconfig.yaml` file in the same directory where you're
running the application. When world generation concludes, Neighborly will write
the final simulation data to a JSON file with the name of the town and the
seed used for random number generation.

```bash
python -m neighborly

# Please use the following command for additional help with running Neighborly's CLI
python -m neighborly --help
```


# Installing for local development

If you wish to download a Neighborly for local development, follow the these instructions.

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

# Running the Tests

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
```

# Running the Samples

Please follow the steps below to run the sample simulations.
We also have examples for using Neighborly in a IPython
notebook and with PyGame.

```bash
# Step 1: Install dependencies for samples
python -m pip install -e ".[samples]"

# Step 2: Run desired sample
python ./samples/<sample_name>.py
```

# Documentation

Neighborly uses [Numpy-style](https://numpydoc.readthedocs.io/en/latest/format.html) docstrings in code and full documentation can be found in the [Wiki](https://github.com/ShiJbey/neighborly/wiki).

When adding docstrings for existing or new bits of code please use the following
references for how to format your contributions:

* [Sphinx Napoleon Plugin for processing Numpy Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
* [Example Numpy Style Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html#example-numpy)


# Contributing

If you are interested in contributing to Neighborly, feel free to fork this repository, make your changes, and submit a pull-request. Please keep in mind that this project is a tool for creativity and learning. We have a [code of conduct](./CODE_OF_CONDUCT.md) to encourage healthy collaboration, and will enforce it if we need to.

**WARNING::** This repository's structure in high flux. Parts of the code get shifted to make the APIs cleaner for use.

Here are some ways that people can contribute to Neighborly:

1. Proposing/Implementing new features
2. Fixing bugs
3. Providing optimizations
4. Fixing typos
5. Filing issues
6. Contributing tutorials/how-tos to the wiki
7. Fixing grammar and spelling in the wiki
8. Creating new samples

## Code Style

Neighborly does not have a set-in-stone code style yet, but I have started integrating
isort, black, and flake8 into the development workflow in VSCode.

You can follow [these instructions](https://black.readthedocs.io/en/stable/integrations/editors.html) for setting up both black and isort. And I found this gist helpful for getting [flake8 working in PyCharm](https://gist.github.com/tossmilestone/23139d870841a3d5cba2aea28da1a895).

# Notes

## Non-Deterministic Behavior

The goal of having a seeded pseudo random simulation is so that users experience deterministic behavior when using the
same starting seed. We try to remove all forms of non-determinism, but some slip through. The known areas are listed
below. If you find any, please make a new issue with details of the behavior.

* Names may not be consistent when using the same seed. Currently, names are generated
  using [Tracery](https://github.com/aparrish/pytracery). We would need to create a custom version that uses an RNG
  instance instead of the global random module to generate names.

## DMCA Statement

Upon receipt of a notice alleging copyright infringement, I will take whatever action it deems
appropriate within its sole discretion, including removal of the allegedly infringing materials.

The repo image is something fun that I made. I love _The Simpsons_, and I couldn't think of anything more neighborly
than Ned Flanders. If the copyright owner for _The Simpsons_ would like me to take it down,
please contact me.

The same takedown policy applies to any code samples inspired by TV shows, movies, and games.
