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

Neighborly is an extensible agent-based settlement simulation. It was built to be a tool for emergent narrative storytelling research. Neighborly generates a virtual settlement and simulates the individual lives of its residents over multiple generations. It models the characters' traits, statuses, relationships, goals, occupations, life events, and more. Neighborly tracks all the life events (starting a new job, falling in love, turning into a demon, etc.), and these become the building blocks for creating emergent stories about characters and their legacies. The entire history of the settlement and its generations of characters is then made available for data analysis or as content for other applications such as games.

Neighborly's was inspired [_Talk of the Town_](https://github.com/james-owen-ryan/talktown), another settlement simulation for emergent narrative storytelling research. And it also draws inspiration from commercial world-simulation games like _Caves of Qud_, _Dwarf Fortress_, _Crusader Kings_, _RimWorld_, and _WorldBox_. It aims to be an easily customizable simulation that can adapt to various narrative settings and support research or entertainment projects.

If you use Neighborly in a project, please [cite this repository](./CITATION.bib).

# Core Features

- 🥸👹👽🏢🏨🏫 Easily create new character/business types
- ⏱️ Time passes in 1-year increments
- 🚀 Utilize a low-fidelity social simulation to simulate hundreds of years of world history within minutes.
- ⚙️ Built using an entity-component system (ECS) architecture
- 📦 Create and share new components and systems using Plugins.
- 🤖 Implement goal-driven behavior using behavior trees and utility AI.
- 👔 Characters can start businesses and hold jobs.
- ️🧬 Give characters traits and statuses that modify their behavior.
- ❤️💔 Model facets of relationships such as romance, friendship, trust, and respect.
- 💥 Simulate random life events that spice up characters' lives.
- ⚖️ Define Social Rules for how characters should feel about each other.
- 🏬 Define location preference rules for what locations characters frequent in a year.
- 📈 Collect and analyze simulation data using industry-standard data science tools like Pandas.
- 📜 Export simulation data to JSON.

# System caveats

- Simulates a single settlement
- Buildings hold either one business or residence. No mixed-use or multifamily housing.
- The internal architecture does not follow "Pure" ECS practices. It mixes ECS and object-oriented programing techniques to provide easy-to-use interfaces.
- Characters can only hold one occupation at a time.
- Does not model the exact position of characters or objects, only buildings.

# Future work

- Add a skill system.
- Add mixed-use buildings and multifamily housing.

# Installation

The latest official release of Neighborly is available to install from [PyPI](https://pypi.org/project/neighborly/).

```bash
pip install neighborly
```

The most recent changes not uploaded to PyPI can be installed directly from GitHub.

```bash
pip install git+https://github.com/ShiJbey/neighborly.git
```

Then you can test if the installation was successful.

```bash
python -m neighborly --version
# Should output the current version number
1.x.x
```

## Installing for local development

If you wish to download a Neighborly for local development or want to play around with
any of the samples, you need to clone or download this repository and install
using the _editable_ flag (-e). Please see the instructions below. This command will install
a Neighborly into the virtual environment along with all its dependencies and a few
additional development and testing dependencies such as _black_, _isort_, and _pytest_.

```bash
# Step 1: Clone Repository and change into project directory
git clone https://github.com/ShiJbey/neighborly.git
cd neighborly

# Step 2 (MacOS/Linux): Create and activate a Python virtual environment
python3 -m venv venv
source ./venv/bin/activate

# Step 2 (Windows): Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Step 3: Install local build and dependencies
python -m pip install -e ".[development,testing]"
```

# Usage

## Exploring the Samples

The best way to learn how to use Neighborly is to explore the various samples in the `samples` directory
that demonstrate how to create custom simulations and collect and visualize data. Interactive samples with the `.ipynb`
extension are meant to be run using [Jupyter Lab](https://jupyter.org/). Please run the following command
to ensure all dependencies are installed for the samples. Make sure that you've activated your Python virtual 
environment beforehand.

```bash
python -m pip install -e ".[samples]"
```

Then, run the following commands to run the sample scripts or notebooks.

```bash
# To run sample scripts, use:
python ./samples/<name_of_sample>.py

# Explore IPython notebooks using Jupyter Lab:
jupyter-lab
```

## Plugins

Plugins are importable Python modules or packages that add new components, resources, and systems.
A few default plugins come prepackaged with Neighborly to help users get started. Users can specify what
plugins to import by changing the names listed in the `plugins` section of a simulation's configuration.
Any changes to the listed plugins must occur before the neighborly instance is constructed, as that is when
plugins are loaded.

Please see the [Plugins](https://shijbey.github.io/neighborly/plugins.html) section of the documentation for more 
information about authoring plugins.

## Command-line interface

Neighborly's command line interface (CLI) generates a world and exports the generated data to JSON. 
By default, Neighborly runs a built-in version of _Talk of the Town_.
Users can configure the simulation settings using config files written in yaml or json. By default, the CLI will
look for a `neighborly.config.yaml` or `neighborly.config.json` file in the current working directory. Users can
specify a path for the CLI to find a config file using the `-c` or `--config` arguments. Users can also control
where the JSON output is stored or turn off JSON output using the `--output` and `--no-output` arguments.

```bash
# Run the default simulation
python -m neighborly

# Load custom config
python -m neighborly --config <path_to_config_file>

# Specify output path
python -m neighborly --output <path_to_write_world_data>

# Disable generating output
python -m neighborly --no-output
```

# Tests

Neighborly uses [PyTest](https://docs.pytest.org/) for unit testing. All tests are located in the `tests/` directory. I
do my best to keep tests updated. However, some tests may need to be
added or updated due to constant breaking changes between releases. If you want to contribute unit tests, please refer
to [CONTRIBUTING.md](./CONTRIBUTING.md).

```bash
# Step 1: Install additional dependencies for tests
python -m pip install -e ".[testing]"

# Step 2: Run Pytest
pytest

# Step3 : (Optional) Generate a test coverage report
pytest --cov=neighborly tests/
```

# Documentation

The most up-to-date documentation can be found at [here](https://shijbey.github.io/neighborly/). The Sphinx docs usually need to catch up to the actual 
codebase. So, when in doubt, please refer to the provided samples and in-code docstrings for assistance.

## Building the documentation

Below are instructions for building Neighborly's documentation using Sphinx. We also provide a `package.json` file
that eases docs development using Node.js. The file contains scripts for building, cleaning, and serving the 
documentation.

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

Contributions are welcome. Please refer to [CONTRIBUTING.md](./CONTRIBUTING.md) for more information about how to get
involved.

# License

This project is licensed under the [MIT License](./LICENSE).

# DMCA Statement

Upon receipt of a notice alleging copyright infringement, I will take whatever action it deems appropriate within its
sole discretion, including removal of the allegedly infringing materials.

The repo image is something fun that I made. I love _The Simpsons_, and I couldn't think of anyone more neighborly than
Ned Flanders. If the copyright owner for _The Simpsons_ would like me to take it down, please contact me. The same
takedown policy applies to code samples inspired by TV shows, movies, and games.
