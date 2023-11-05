.. neighborly documentation master file, created by
   sphinx-quickstart on Sat Nov  4 22:34:51 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to neighborly's documentation!
======================================

Neighborly is an extensible agent-based settlement simulation. It was built to be a tool for emergent narrative storytelling research. Neighborly generates a virtual settlement and simulates the individual lives of its residents over multiple generations. It models the characters' traits, statuses, relationships, occupations, life events, and more. Neighborly tracks all the life events (starting a new job, falling in love, turning into a demon, etc.), and these become the building blocks for creating emergent stories about characters and their legacies. The entire history of the settlement and its generations of characters is then made available for data analysis or as content for other applications such as games.

Neighborly's was inspired `Talk of the Town <https://github.com/james-owen-ryan/talktown>`_, another settlement simulation for emergent narrative storytelling research. It also draws inspiration from commercial world-simulation games like Caves of Qud, Dwarf Fortress*, Crusader Kings, RimWorld, and WorldBox. It aims to be an easily customizable simulation that can adapt to various narrative settings and support research or entertainment projects.

How to use this wiki
--------------------

This wiki explains the core building blocks of Neighborly and how to get started simulating your own procedurally generated settlements. If you're looking for a tutorial or would like to try Neighborly without downloading it, we recommend that people try this `Google Colab notebook <https://colab.research.google.com/drive/1WxZnCR8afekfBl-vI6WcIcS6OhRGdkam?usp=sharing>`_.

Problems with the wiki
----------------------

If you notice any error within the wiki, please file an issue and state where the repository maintainers can find the error. Errors can be anything ranging from typos to sample code that doesn't work. Thank you for helping to make Neighborly a tool for people to learn and experiment with.

Installation
------------

Neighborly is available to download from PyPI. Please use the following command to install the latest release.

.. code-block:: bash

   python3 -m pip install neighborly


If you plan to use Neighborly as a dependency within a larger project. It is recommended that you specify the specific release in your ``pyproject.toml`` or ``requirements.txt`` files. For example, ``neighborly==2.*``. Neighborly's function and class interfaces may change drastically between releases, and this will prevent errors from appearing in your code if an updated version of Neighborly breaks something you rely on.

Neighborly's core content types
-------------------------------

Neighborly is a data-driven framework. So, before we can generate a settlement and simulate the characters' lives, we need to feed the simulation content that it can use. We refer to each piece of content as a content definition.

- :ref:`settlements`: Different types of settlements that could be generated.
- :ref:`businesses`: Places where characters work.
- :ref:`traits`: Represent characters' personalities, relationship statuses, faction affiliations, etc.
- :ref:`relationships`: Track how characters feel about other characters.
- :ref:`skills`: Skills that characters can cultivate during their lives
- :ref:`residences`: Places where characters live
- :ref:`characters`: The characters that make everything run
- :ref:`life_events`: Events that implement character behaviors

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   settlements
   characters
   businesses
   residences
   relationships
   traits
   skills
   effects-and-preconditions
   life_events
   location-preferences
   plugins
   ecs
   api/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
