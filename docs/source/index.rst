Welcome to Neighborly's documentation!
======================================

**Neighborly** is a Python framework for developing agent-based social simulations.
It helps users simulate something akin to the simulations seen in games like
*Dwarf Fortress*, *Rim World*, or *Crusader Kings*. Each character is
represented as an individual autonomous agent that can make actions, respond
to event in their their social networks, and experience various life events.

Our goal with Neighborly is to allow users to simulate backstories of NPCs
(non-player characters) living in a settlement like a town. Neighborly is designed
to simulate longer periods of time (months to decades) at a lower-fidelity
compared to something like *The Sims*.

Neighborly is an experiment in emergent narrative authoring. It places users in
control of what kind of characters, places, and businesses exist in the
settlement. This process can be daunting, so we try to make your life easier
by offering built-in content plugins to help you get started. We can't wait
to see what you make with Neighborly!

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

    neighborly

Neighborly comes preconfigured with a simulation of a small town. Characters
move in and out of the town, start businesses, work jobs, start families,
and get into a number of scenarios with each other. Character activity is
printed to the console (unless otherwise specified). At the end of the
simulation, neighborly will write the state of the simulation to a ``*.json``
file.

We are working on a visualization interface for neighborly.

Contents
========

.. toctree::
    :maxdepth: 2

    installation.rst
    commandline_tool.rst
    working_with_ecs.rst
    plugins.rst
    content_management.rst
    characters.rst
    businesses.rst
    residences.rst
    relationships.rst
    social_rules.rst
    location_biases.rst
    statuses.rst
    events_and_actions.rst
    tracking_backstories.rst
    data_collection.rst
    design_justifications.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
