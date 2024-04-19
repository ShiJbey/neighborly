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
  <a href="https://neighborly.readthedocs.io/en/latest/index.html">Documentation</a> |
  <a href="https://pypi.org/project/neighborly">PyPI</a> | <a href="https://github.com/ShiJbey/neighborly">GitHub</a>
</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/neighborly" alt="PyPI version badge">
  <img src="https://img.shields.io/pypi/pyversions/neighborly" alt="Supported Python Versions badge">
  <img src="https://img.shields.io/pypi/l/neighborly" alt="MIT License badge">
  <img src="https://img.shields.io/pypi/dm/neighborly" alt="PyPI downloads badge">
  <img src="https://img.shields.io/badge/code%20style-black-black" alt="Black formatter badge">
  <img src="https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336" alt="ISort badge">
</p>

Neighborly is an agent-based settlement simulation that generates backstory data for characters living in a procedurally generated settlement. It was built to be a tool for emergent narrative storytelling research. Neighborly models the characters' traits, statuses, relationships, occupations, life events, etc. over decades of simulated time. The entire history of the settlement and its generations of characters is made available for data analysis and exporting. Neighborly aims to be an easily customizable simulation that can adapt to various narrative settings and support research or entertainment projects.

Neighborly's was inspired [_Talk of the Town_](https://github.com/james-owen-ryan/talktown), another settlement simulation for emergent narrative storytelling research. It also draws inspiration from commercial world-simulation games like _Caves of Qud_, _Dwarf Fortress_, _Crusader Kings_, _RimWorld_, and _WorldBox_.

If you use Neighborly in a project, please [cite this repository](./CITATION.bib). You can read
Neighborly's associated [paper](https://shijbey.github.io/publications/Neighborly.pdf) that was published in the
proceedings of the 2022 IEEE Conference On Games.

> [!IMPORTANT]
> Neighborly's current architecture differs from what is described in the paper. Please see the [Differences from the Paper](#ℹ️-differences-from-the-paper) section below.

## 🎯 Core Features

- 💾 Data-driven simulation
- 🛠️ Procedurally generates a settlement, districts, characters, residences, and businesses.
- 📦 Plugin system to load and share new content.
- 👔 Characters can start businesses and hold jobs.
- ️🏷️ Tag GameObjects with traits that modify their stats and relationships.
- ❤️ Characters cultivate relationships based on romance and reputation.
- 💥 Simulate random life events that spice up characters' lives.
- ⚖️ Social Rules influence how characters feel about each other.
- 🏬 Location Preferences determine what locations characters frequent.
- 📈 Query simulation data using SQL and analyze data with data science tools like [Pandas](https://pandas.pydata.org/).

## 🚀 How to Install

The latest official release of Neighborly is available to install from [PyPI](https://pypi.org/project/neighborly/).

```bash
pip install neighborly
```

### Try Neighborly Without Installing

Neighborly is available to use within this [sample Google Colab notebook](https://colab.research.google.com/drive/1WxZnCR8afekfBl-vI6WcIcS6OhRGdkam?usp=sharing). It contains a basic walkthrough of how to define content for the simulation and inspect the generated data.

### Installing for Local Development

To download a Neighborly for local development or play around with any of the samples, you need to clone or download this repository and install it using the _editable_ flag (-e). Please see the instructions below. This command will install a Neighborly into the virtual environment along with all its dependencies and a few additional development and testing dependencies such as _black_, _isort_, and _pytest_.

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

# Step 3: Install neighborly and dependencies
python -m pip install -e ".[development]"
```

## 🍪 Running the Samples

Example simulations can be found in the `samples` directory. These demonstrate how to create simulations and collect and visualize data. We provide command line scripts and interactive IPython notebooks.

First, follow the [Installing for Local Development](#installing-for-local-development) instructions provided above. Then the commands below will get you started with running the sample simulations.

```bash
# Step 1: Install neighborly locally and all the dependencies needed to run the sample content.
python -m pip install -e ".[samples]"

# Step 2a: (optional) To run sample scripts
python ./samples/NAME_OF_SAMPLE_FILE.py

# Step 2b: (optional) To run IPython (*.ipynb) notebooks
jupyter-lab
```

## 🧪 Running the Tests

Neighborly uses [PyTest](https://docs.pytest.org/) for unit testing. All tests are located in the `tests/` directory.

```bash
# Step 1: Install additional dependencies for testing and development
python -m pip install -e ".[development]"

# Step 2: Run Pytest
pytest

# Step 3: (Optional) Generate a test coverage report
pytest --cov=neighborly tests/
```

## 📚 Documentation

Neighborly's documentation can be found at [Read the Docs](https://neighborly.readthedocs.io/en/latest/index.html).

## 🤝 Contributing

Contributions are welcome. Please refer to [CONTRIBUTING.md](./CONTRIBUTING.md) for more information about how to get involved.

## 📄 License

This project is licensed under the [MIT License](./LICENSE).

## ℹ️ Differences from the Paper

- **Directed relationships only** -  Neighborly only supports directed relationships that track how one character feels about another. Support for reciprocal relationships was removed because it complicated the simulation by forcing users to check multiple locations for relationship data.
- **No activity/service system** - The activity system was introduced to help characters decide where to frequent outside of work/home. This system was replaced with _location preferences_, which are more flexible. The activity system can be emulated by associating certain traits with locations.
- **No 7-day weekly routines** - Routines were tedious to create and became irrelevant when Neighborly's time step scale changed from incrementing the date by a few hours to incrementing by a single month.
- **No direct support for differing AI strategies** - We intended to support various character decision-making algorithms but made behavior authoring too tedious and took emphasis away from the content authoring and data generation aspects of Neighborly.
- **Event system replaced with action objects and utility scores** - Since Neighborly does not need to support user-supplied character decision-making logic, it made behavior modeling much simpler. The old life event system required users to specify event effects for each different type of agent, and this naturally complicated things. Currently, agent behavior is implemented using a combination of Systems, actions, and life events.
- **No behavior trees** - Behavior trees added complexity to the system. It was removed to simplify things.
- **No character values** - Over time, the character value system and personality models were combined into a single stat system. Removing them simplified much of the agent modeling and allowed for the most flexibility.
- **No character movement** - Characters do not move between locations. This added additional processing overhead and became unnecessary when moving to a one-month time steps.

## ©️ DMCA Statement

Upon receipt of a notice alleging copyright infringement, I will take whatever action it deems appropriate within its sole discretion, including removal of the allegedly infringing materials.

The repo image is something fun that I made. I love _The Simpsons_, and I couldn't think of anyone more neighborly than Ned Flanders. If the copyright owner for _The Simpsons_ would like me to take it down, please contact me. The same takedown policy applies to code samples inspired by TV shows, movies, and games.
