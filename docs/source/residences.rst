Residences
==========

Residences are another special type of location that characters own and live in. They are
represented as GameObjects that have a ``Residence`` component. When characters move into a
settlement, a new residence is created for them or they are given an existing vacant residence.
During the course of characters' lives, they are fre to travel to residences, move from one
residence to another, and abandon them altogether.

Currently, residences are probably the most under utilized entity in the simulation. There is only
one residence prefab definition in use, and thats a single-family house. There are plans to expand
the offering of residences to multi-family homes such as duplexes and apartment buildings or
multi-use housing where businesses and residences share a building.

Modeling residences
-------------------

Residences like other GameObjects are a collection of components. Some components are
required for residences to function properly. The following is a list of components
currently used to drive residences.

- ``Residence``: Tags a GameObject as a residence where characters can live. The Residence component
  tracks a set of characters that live in the residence, and a set of characters that own the
  residence. This is to differentiate adults who own residences from their children who are also
  a residents, but do not own the residence
- ``Location``: Marks the residence as a location that characters can travel to. It tracks what
  characters are present at the location at any given time
- ``StatusManager``: Tracks any statuses such as ``Vacant`` that may be attached to a residence.
  This is a common component used across GameObjects for status management.
- ``EventHistory``: Tracks a history of events that this residence was involved with.
- ``Building``: If the residence is the entire building, then it will have a Building component
  that describes the the style of building that the residence is in. Usually this is a "residential"
  building.
- ``CurrentLot``: This component is added automatically by the simulation when a GameObject with a
  Building component is added to the settlement.

Residence statuses
^^^^^^^^^^^^^^^^^^

- ``Vacant``: This status is used to tag residences that don't have any one living there.


Defining a residence prefab
---------------------------

.. code-block:: yaml

    name: "residence::default::house"
    components:
      Residence: { }
      Location: { }
      Position2D: { }
      StatusManager: { }
      EventHistory: { }
      Building:
          building_type: residential

Loading the prefab
------------------

You can add your prefab to the simulation using loader functions included with
Neighborly.

1. ``load_residence_prefab(sim.world, "path/to/yaml/file")``
2. ``load_data_file(sim.world, "path/to/yaml/file")``

There is a slight difference between these two functions. The first is intended to load
a single residence prefab from a file. That is what we would use for the example
definition above. However, if we placed multiple residence prefabs in the same file,
the second function would load them all at once. The only change we would need to make
the second option work is to place our definitions within a YAML list (see below).
You can alays reference the included plugin code to get a better understanding of how
to use these functions.

.. code-block:: yaml

    Residences:
        - name: "House"
          # Other data fields ...
        - name: "Mansion"
          # ...
        - name: "Shack"
          # ...
