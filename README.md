<h1 align="center">
  <img
    width="150"
    height="150"
    src="https://user-images.githubusercontent.com/11076525/165836171-9ffdea6e-1633-440c-be06-b46e1e3e4e04.png"
  >
  <br>
  Neighborly
</h1>

<p align="center">
  <img src="https://img.shields.io/pypi/v/neighborly">
  <img src="https://img.shields.io/pypi/pyversions/neighborly">
  <img src="https://img.shields.io/pypi/l/neighborly">
  <img src="https://img.shields.io/pypi/dm/neighborly">
  <img src="https://img.shields.io/badge/code%20style-black-black">
  <img src="https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336">
</p>

# Overview

Neighborly is an extensible, data-driven, agent-based modeling framework
designed to simulate towns of characters for games. It is intended to be a
tool for exploring simulationist approaches to character-driven emergent
narratives. Neighborly's simulation architecture is inspired by roguelikes
such as _Caves of Qud_ and _Dwarf Fortress_.

Currently, Neighborly works best as a narrative data generator. It models
characters’ lives, jobs, routines, relationships, and life
events. All of these parts are harnessed to produce
emergent character backstories as they interact with each other, grow, and
change. You can even specify custom characters, businesses, residences,
occupations, life events, social rules, and more. Neighborly is meant to
be customized to the narrative setting of your creative vision. Check out the
samples directory to see how we modeled the popular anime, _Demon Slayer_.

Neighborly was inspired by lessons learned from working with
[_Talk of the Town_](https://github.com/james-owen-ryan/talktown)
and aims to give people better documentation, simpler interfaces, and more
opportunities for extension and content authoring.

# Core Features

- Data-driven
- Add custom character prefabs
- Add custom business prefabs
- Define life events and actions to drive narrative generation
- Define social rules for how characters should feel about each other
- Define rules for where characters what locations characters should frequent
- Specify goal-driven behaviors using behavior trees and utility AI
- Can model various relationship facets like romance, friendship, trust, and respect
- Collect and export data about agents using Pandas DataFrames
- Commandline interface (CLI) tool
- Create plugins to modularize and share custom content
- Export simulation state to JSON
- Could be integrated with roguelike development tools like [tcod](https://github.com/libtcod/python-tcod)

## Not yet supported features

- Generating characters with a subset of character traits randomly selected from a
  pool of traits

# Installation

Neighborly is available to install from
[PyPI](https://pypi.org/project/neighborly/). This will install the latest
official release.

```bash
pip install neighborly
```

If you want to install the most recent changes that have not been uploaded to
PyPI, you can install it by cloning the main branch of this repo and installing that.

```bash
pip install git+https://github.com/ShiJbey/neighborly.git
```

## Installing for local development

If you wish to download a Neighborly for local development or want to play around with
any of the samples, you need to clone or download this repository and install
using the _editable_ flag (-e). Please see the instructions below. This will install
a Neighborly into the virtual environment along with all its dependencies and a few
addition development dependencies such as _black_ and _isort_ for code formatting.

```bash
# Step 1: Clone Repository and change into project directory
git clone https://github.com/ShiJbey/neighborly.git
cd neighborly

# Step 2 (MacOS/Linux): Create and activate a python virtual environment
python3 -m venv venv
source ./venv/bin/activate

# Step 2 (Windows): Create and activate a python virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Step 3: Install local build and dependencies
python -m pip install -e ".[development,testing]"
```

# Usage

If you want examples of how to use Neighborly and how to extend it
with custom content, please refer to
[Neighborly's docs](https://shijbey.github.io/neighborly/) and the sample scripts
in the [`samples` directory](https://github.com/ShiJbey/neighborly/tree/main/samples).

## Using as a library

Neighborly can be used as a library within a Python script or package.
The `samples` directory contains python scripts that use Neighborly this
way. Please refer to them when creating new Plugins and other content.

## Writing plugins

Users can extend Neighborly's default content/behavior using plugins.
A few default plugins come prepackaged with Neighborly to help people get
started. Plugins are implemented as Python packages or modules and are
imported by passing their name in the `plugins` section of the configuration.

Please see the [Plugins](https://shijbey.github.io/neighborly/plugins.html)
section of the documentation for more information about authoring plugins.

## Running the CLI

Neighborly can be run as a module `$ python -m neighborly` or commandline `$ neighborly`
script. If you require additional help while running, please use
`$ python -m neighborly --help` or `$ neighborly --help`.

By default, Neighborly runs a builtin version of **Talk of the Town**. However, you can
configure the simulation settings by creating a `neighborlyconfig.yaml` file in
the same directory where you're running the CLI.

When world generation concludes, Neighborly can write the final simulation data
to a JSON file with the seed used for world generation.

## Running the Samples

Neighborly provides sample simulations to show users how to customize
it to create new story world themes.

```bash
# Make sure that you've activated your python virtual environment
# Replace <sample_name>.py with the name of the
# sample you want to run
python ./samples/<sample_name>.py
```

The samples in the `notebooks` directory require Jupyter to be installed. So you will
need to run the following command to install all the needed dependencies.

```bash
python -m pip install -e ".[samples]"
```

Then start Jupyter and pass the relative path to the `notebooks` directory. The following
assumes that the command is being run from the root of the project.

```bash
notebook ./samples/notebooks
```

## Running the Tests

Testing is very important. It is how we are able to ensure that new changes don't
break anything. I do my best to keep tests updated, but some tests may be out of
date and refer to systems and logic that no longer exist in Neighborly.

Feel free to contribute tests by forking the repo, adding your test(s), and
submitting a pull request with a description of your test cases. Your commits
should only contain changes to files within the `tests` directory. If you
change any files in other parts of the project, your PR will be rejected.

Please follow the steps below to run Neighborly's test suite. Neighborly uses
[PyTest](https://docs.pytest.org/en/7.1.x/) to handle unit testing.

```bash
# Step 1: Install dependencies for tests
python -m pip install -e ".[testing]"

# Step 2: Run Pytest
pytest

# Step3 : (Optional) Generate a test coverage report
pytest --cov=neighborly tests/
```

# Documentation

The most up-to-date documentation can be found [here](https://shijbey.github.io/neighborly/)

Neighborly uses [Numpy-style](https://numpydoc.readthedocs.io/en/latest/format.html)
docstrings in code. When adding docstrings for existing or new bits of code please use the following
references for how to format your contributions:

- [Sphinx Napoleon Plugin for processing Numpy Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html)
- [Example Numpy Style Docstrings](https://www.sphinx-doc.org/en/master/usage/extensions/example_numpy.html#example-numpy)

## Building the documentation

Neighborly's docs are built using Sphinx. Below are instructions for building the docs

```bash

# Install the documentation dependencies
python -m pip install -e ".[docs]"

# Build docs as HTML
sphinx-apidoc -o docs/source/module_docs/ src/neighborly
sphinx-build -b html docs/source/ docs/build/html
```

If you happen to have _npm_ installed, you can use the `package.json` configuration file to
run build, clean build output, and run a test HTTP server.

# Contributing

Here are some ways that people can contribute to Neighborly:

1. Proposing/Implementing new features
2. Fixing bugs
3. Providing optimizations
4. Filing issues
5. Contributing tutorials and how-to guides
6. Fixing grammar and spelling
7. Creating new samples and plugins

If you are interested in contributing to Neighborly, there are multiple ways to get
involved, and not all of them require you to be proficient with GitHub. Interested
parties can contribute to the core code base of Neighborly and create new content
in the way of plugins. I love feedback, and if you have any questions, create a new
issue, and I will do my best to answer. If you want to contribute to the core code,
free to fork this repository, make your changes, and submit a pull-request with a
description of your contribution. Please keep in mind that this project is a
tool for creativity and learning. I have a [code of conduct](./CODE_OF_CONDUCT.md) to
encourage healthy collaboration, and will enforce it if I need to.

# Code Style

Neighborly uses [_Black_](https://black.readthedocs.io/en/stable/) to handle code style
and sorts imports using [_isort_](https://pycqa.github.io/isort/).

# DMCA Statement

Upon receipt of a notice alleging copyright infringement, I will take whatever action it
deems appropriate within its sole discretion, including removal of the allegedly
infringing materials.

The repo image is something fun that I made. I love _The Simpsons_, and I couldn't think
of anyone more neighborly than Ned Flanders. If the copyright owner for _The Simpsons_
would like me to take it down, please contact me. The same takedown policy applies to
any code samples inspired by TV shows, movies, and games.
