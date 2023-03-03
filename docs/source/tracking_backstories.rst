Tracking Backstories
====================

As characters progress through the simulation, they will have the opportunity
to engage in various events. These events make up their personal backstories
and we track this data for every character in the simulation.

Event History
-------------

All the events that have occurred in the simulation are stored in a shared,
``AllEvents`` resource within the World instance. Each character is given an
``EventHistory`` component that tracks the IDs of events that the character was
a part of. You can use these IDs to retrieve the events from the shared resource
using the ``get_events_for()`` utility function and pass the character as a
parameter.

Work History
------------

This is a specialized subset of data that tracks what occupations characters
have had, how long, and why they left that job. Think of it like their resume. It
is mainly used in precondition calculations for various occupations. Without this
component, we would have to calculate characters' work histories from the events
in their ``EventHistory`` components

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    installation.rst
    working_with_ecs.rst
    relationships.rst
    event_driven_architecture.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
