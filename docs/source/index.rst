Welcome to Neighborly's documentation!
======================================

**Neighborly** is a Python framework for agent-based social simulation in games.
It helps users simulate something akin to the settlement simulations seen in games like
*Dwarf Fortress*, *Rim World*, or *Caves of Qud*. Each character is
represented as an individual autonomous agent that can make actions, respond
to events, form relationships, work a job, etc. Neighborly is ideal for modeling
background world simulations or pre-generating data for background characters. It's
architecture was heavily inspired by Roguelike games.

Neighborly is an experiment in simulationist emergent narrative authoring. Our aim was
to produce an approachable interface for authoring town-scale social simulations
intended for games or narrative generation. Therefore, agents that are by default
modeled with more narratively interesting data than what someone would find in other
agent-based modeling frameworks like `Mesa <https://mesa.readthedocs.io/en/stable/#>`_
or `NetLogo <https://ccl.northwestern.edu/netlogo/>`_.

Neighborly places users in control of what kind of characters, places, and things exist
in the settlement. This process can be daunting, so we try to make your life easier
by offering built-in content plugins to help you get started.

We can't wait to see what you make with Neighborly!

Installation
------------

Neighborly is available to install from PyPI. This will install the latest official
release.

.. code-block:: console

    pip install neighborly


If you want to install the most recent changes that have not been uploaded to
PyPI, you can install it by cloning the main branch of this repo and installing that.

.. code-block:: console

    pip install git+https://github.com/ShiJbey/neighborly.git


Running the sample simulation
-----------------------------

.. code-block:: console

    python -m neighborly

Neighborly comes preconfigured with a simulation of a small town. Characters
move in and out of the town, start businesses, work jobs, start families,
and get into a number of scenarios with each other.

All Character activity is printed to the console. And when the simulation ends,
neighborly will export all the generated simulation data to a ``*.json`` file.

.. Contents
.. ========

.. toctree::
    :maxdepth: 1
    :hidden:
    :titlesonly:

    installation
    commandline_tool
    working_with_ecs
    plugins
    characters
    locations
    businesses
    residences
    relationships
    social_rules
    location_biases
    life_events
    goals_and_actions
    statuses
    settlements
    routines
    tracking_backstories
    data_collection
    design_justifications
    module_docs/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
