.. neighborly documentation master file, created by
   sphinx-quickstart on Sat Nov  4 22:34:51 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Neighborly's documentation!
======================================

Neighborly is an agent-based settlement simulation for emergent narrative storytelling and data analysis. It simulates generations of characters living within a village/town/city with a particular focus on their relationships and life events (starting a new job, falling in love, turning into a demon, etc.). It combines social simulation elements, like relationship tracking, with RPG elements, such as character stats and skills, to generate backstories about characters and their families.
Neighborly simulates characters' traits, statuses, relationships, occupations, and life events and makes the entire simulated history available for data analysis and game development.

Neighborly's was inspired by `Talk of the Town <https://github.com/james-owen-ryan/talktown>`_ and aims to be a more customizable and user-friendly alternative to support research or entertainment projects. It also draws inspiration from commercial simulation-driven emergent narrative games like *Caves of Qud*, *Dwarf Fortress*, *Crusader Kings*, *RimWorld*, and *WorldBox*.

How to use these docs
---------------------

This wiki explains the core building blocks of Neighborly and how to get started simulating your own procedurally generated settlements. If you're looking for a tutorial or would like to try Neighborly without downloading it, here is a `Google Colab notebook <https://colab.research.google.com/drive/1WxZnCR8afekfBl-vI6WcIcS6OhRGdkam?usp=sharing>`_ that covers the basics of Neighborly.

What if I find errors?
----------------------

If you notice any errors with sample code or typos within the docs, please file a GitHub issue stating the issue. We appreciate your help in making Neighborly an accessible tool for learning and experimentation.

Installation
------------

Neighborly is available to install from PyPI. Please use the following command to install the latest release.

.. code-block:: bash

   python3 -m pip install neighborly


We recommend that users specify a specific Neighborly release in their ``pyproject.toml`` or ``requirements.txt`` files. For example, ``neighborly==2.*``. Neighborly's function and class interfaces may change drastically between releases, and this will prevent errors from appearing in your code if an updated version of Neighborly breaks something you rely on.

Neighborly's core content types
-------------------------------

Neighborly is a data-driven. So, user's need to feed it a decent amount of data to get diverse and interesting results. However, Neighborly makes it easy for people to start simulating with a small amount of data and gradually add more. Below are the main content types that users can define.

- :ref:`settlements`: The overall place where characters live and start businesses.
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
