# Neighborly: OpenSource Town-Scale Social Simulation

![Neighborly Screenshot in pygame](./docs/resources/pygame_sample_screenshot.png)

Neighborly is a framework that simulates characters in a virtual town. It takes lessons learned from working with
[_Talk of the Town_](https://github.com/james-owen-ryan/talktown)
and gives people better documentation, simpler interfaces, and more opportunities for extension and content authoring.

## How to use

In the `samples` directory you can find examples of how to create and run a Neighborly simulation instance. To run
these, you need download or clone this repository locally, install the dependencies, and install a development build.

```bash
# Step One: Clone Repository
git clone https://github.com/ShiJbey/neighborly.git

# Step Two (Optional): Create and activate python virtual environment
cd neighborly

# For Linux and MacOS
python3 -m venv venv
source ./venv/bin/activate

# For Windows
python -m venv vev
./venv/Scripts/Activate

# Step Three: Install local build and dependencies
python -m pip install -e .
```

## Running the Tests

Please follow the steps for how to use then run the following to download the dependencies for running tests.

```bash
python -m pip install -e ".[tests]"
```

Then just enter `pytest` intp the commandline.

## Running the Samples

Please follow the steps for how to use then run the following to download the dependencies for running the samples.

```bash
python -m pip install -e ".[samples]"
```

Now you may execute any of the tests using `python ./samples/<sample_name>.py`.

## Notes

### Non-Deterministic Behavior

The goal of having a seeded pseudo random simulation is so that users experience deterministic behavior when using the
same starting seed. We try to remove all forms of non-determinism, but some slip through. The known areas are listed
below. If you find any, please make a new issue with details of the behavior.

- Names may not be consistent when using the same seed. Currently, names are generated
  using [Tracery](https://github.com/aparrish/pytracery). We would need to create a custom version that uses an RNG
  instance instead of the global random module to generate names.
