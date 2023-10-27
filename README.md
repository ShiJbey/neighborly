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

Neighborly is an extensible agent-based settlement simulation. It was built to be a tool for emergent narrative storytelling research. Neighborly generates a virtual settlement and simulates the individual lives of its residents over multiple generations. It models the characters' traits, statuses, relationships, occupations, life events, and more. Neighborly tracks all the life events (starting a new job, falling in love, turning into a demon, etc.), and these become the building blocks for creating emergent stories about characters and their legacies. The entire history of the settlement and its generations of characters is then made available for data analysis or as content for other applications such as games.

Neighborly's was inspired [_Talk of the Town_](https://github.com/james-owen-ryan/talktown), another settlement simulation for emergent narrative storytelling research. It also draws inspiration from commercial world-simulation games like _Caves of Qud_, _Dwarf Fortress_, _Crusader Kings_, _RimWorld_, and _WorldBox_. It aims to be an easily customizable simulation that can adapt to various narrative settings and support research or entertainment projects.

If you use Neighborly in a project, please [cite this repository](./CITATION.bib). You can read a copy of
Neighborly's associated [paper](https://shijbey.github.io/publications/Neighborly.pdf) that was published in the
proceedings of the 2022 IEEE Conference On Games. ⚠️ **Warning**: Please note that Neighborly's current structure
differs greatly from the version the paper describes.

# Core Features

- 🏙️ Procedurally generates a settlement and the history of its residents.
- 🚀 Utilize a low-fidelity social simulation to simulate hundreds of years of world history within minutes.
- ⚙️ Built using an entity-component system (ECS) architecture
- 📦 Plugin system to load and share new content.
- 👔 Characters can start businesses and hold jobs.
- ️🧬 Characters have traits that modify their stats and relationships.
- ❤️ Characters form and cultivate relationships based on romance and reputation.
- 💥 Simulate random life events that spice up characters' lives.
- ⚖️ Define Social Rules for how characters should feel about each other.
- 🏬 Define location preference rules for what locations characters frequent.
- 📈 Uses [Polars](https://www.pola.rs) for fast data analysis.
- 📜 Export simulation data to JSON.

# System caveats

- Only simulates a single settlement
- Characters can only hold one occupation at a time.
- Does not model the exact position of entities.

# Installation

The latest official release of Neighborly is available to install from [PyPI](https://pypi.org/project/neighborly/).

```bash
pip install neighborly
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

# Plugins

Plugins are importable Python modules or packages that add new content to a simulation. They allow users to change
a simulation's behavior without editing the core library code. All plugins should have a top-level
`load_plugin(sim)` function that gets called to load in the plugin content.

As with any piece of software, always express caution when downloading third-party plugins. Ensure they come from a
source that you trust.

To read more about plugins, visit the [Plugins](https://github.com/ShiJbey/neighborly/wiki/plugins) section of the
wiki.

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

The best place to find examples of how to use Neighborly is actually in the `./tests` directory. There you will find examples of loading content from files, running a simulation, and saving the output to JSON. There is also the [wiki](https://github.com/ShiJbey/neighborly/wiki). However, the wiki has a tendency to be out of date when new, potentially breaking changes are made to the framework. However, unit tests are updated almost every time a new feature is added.

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
