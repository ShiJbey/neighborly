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

Neighborly is an extensible agent-based modeling framework for exploring social simulation-driven emergent narrative
storytelling. It procedurally generates a virtual settlement and simulates the individual lives of its residents over
multiple generations. Neighborly models characters' traits, statuses, relationships, goals, occupations, life events,
and more. The characters experience various _Life Events_ such as starting a new job, dating someone, having a child,
growing older, and more. Neighborly tracks all these events, which become the building blocks of emergent narratives.
The entire history of the settlement and the characters is then made available for data analysis or as content for other
applications such as games.

Neighborly's was inspired by [_Talk of the Town_](https://github.com/james-owen-ryan/talktown), and its
architecture is inspired by games like _Caves of Qud_, _Dwarf Fortress_, and _WorldBox_. Its goal is to be a
customizable social simulation that can adapt to various narrative settings.

If you use Neighborly in a project, please [cite this repository](./CITATION.bib).

# Core Features

- 🚀 Utilizes a low-fidelity social simulation allowing it to simulate hundreds of years of world history within minutes.
- 👔 Characters can start businesses and hold jobs
- 📦 Users can create and share custom content plugins to extend Neighborly's capabilities
- 🤖 Characters follow goal-driven behaviors defined using behavior trees and utility AI
- ️🧬 Traits and statuses modify character behavior
- ❤️💔 Models facets of relationships such as romance, friendship, trust, and respect
- 💥 Random Life Events spice up characters' lives
- ⚖️ Social Rules define how characters should feel about each other
- 🏬 Location Preference Rules define rules for what locations characters should frequent
- 📈 Collect and analyze simulation data using DataFrames
- 📜 Export simulation data to JSON

# Installation

The latest official release of Neighborly is available to install from [PyPI](https://pypi.org/project/neighborly/).

```bash
pip install neighborly
```

The most recent changes that have not been uploaded to PyPI can be installed directly from GitHub.

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

## Exploring the Samples

The best way to learn how to use Neighborly is to explore the various samples in the `samples` directory
that demonstrate how to create custom simulations and collect and visualize data. Interactive samples with the `.ipynb`
extension are meant to be run using [Jupyter](https://jupyter.org/). Please run the following command to ensure all
dependencies are installed for the samples. Make sure that you've activated your Python virtual environment.

```bash
python -m pip install -e ".[samples]"
```

## Writing plugins

Users can extend Neighborly's default content/behavior using plugins. A few default plugins come prepackaged with
Neighborly to help people get started. Plugins are implemented as Python packages or modules and are imported by adding
their name in the `plugins` section of a simulation's configuration.

Please see the [Plugins](https://shijbey.github.io/neighborly/plugins.html) section of the documentation for more
information about authoring plugins.

## Command line interface

Neighborly's command line interface (CLI) generates a world for a specified amount of virtual
time and exports the generated data to JSON. By default, Neighborly runs a built-in version of **Talk of the Town**.
Users can configure the simulation settings by creating a `neighborlyconfig.yaml` file.

Neighborly can be run as a module `$ python -m neighborly` or command line `$ neighborly` script. If you require
additional help, please use `$ python -m neighborly --help` or `$ neighborly --help`.

# Tests

Neighborly uses [PyTest](https://docs.pytest.org/) for unit testing. All tests are located in the `tests/` directory. I
do my best to keep tests updated. However, due to constant breaking changes between releases, some tests may need to be
added, updated, or refer to code that no longer exists. If you want to contribute unit tests, please refer
to [CONTRIBUTING.md](./CONTRIBUTING.md).

```bash
# Step 1: Install dependencies for tests
python -m pip install -e ".[testing]"

# Step 2: Run Pytest
pytest

# Step3 : (Optional) Generate a test coverage report
pytest --cov=neighborly tests/
```

# Documentation

The most up-to-date documentation can be found at [here](https://shijbey.github.io/neighborly/).

## Building the documentation

Below are instructions for building Neighborly's documentation using Sphinx. You can use the `package.json` file to
build, clean, and serve the documentation if you have `npm` installed.

```bash

# Install the documentation dependencies
python -m pip install -e ".[docs]"

# Build docs as HTML (Run these commands from the projects root folder)
sphinx-apidoc -o docs/source/module_docs/ src/neighborly
sphinx-build -b html docs/source/ docs/build/html
```

# Getting help and submitting bug reports

If you have any questions, feedback, or problems, please create a new Issue. I will do my best to answer as soon as I
can. Please be respectful, and I appreciate your patience.

# Contributing

Contributions are welcome. Please refer to [CONTIBUTING.md](./CONTRIBUTING.md) for more information about how to get
involved.

# License

This project is licensed under the [MIT License](./LICENSE).

# DMCA Statement

Upon receipt of a notice alleging copyright infringement, I will take whatever action it deems appropriate within its
sole discretion, including removal of the allegedly infringing materials.

The repo image is something fun that I made. I love _The Simpsons_, and I couldn't think of anyone more neighborly than
Ned Flanders. If the copyright owner for _The Simpsons_ would like me to take it down, please contact me. The same
takedown policy applies to code samples inspired by TV shows, movies, and games.
