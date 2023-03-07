Residences
==========

Residences are the GameObjects that characters live-in. So characters can travel to
them, change residences from one to another, and abandon them altogether.

Currently, residences are probably the most under utilized entity in the simulation.
There is only one residence prefab definition in use, and thats a single-family house.

*Talk of the Town* featured apartment complexes as well as single-family homes, but I
have not gotten around to modeling them yet. However, they could be represented with
a prefab that contains multiple residences (apartment units) as child prefabs.

Residence Components
--------------------

Residences like other GameObjects are a collection of components. Some components are
required for residences to function properly. The following is a list of components
currently used to drive residences.

- ``Residence``: Marks th GameObject as a residence where characters can live
- ``Location``: Marks the residence as a location that characters can travel to
- ``StatusManager``: Tracks any statuses such as ``Vacant`` that may be attached to the
  GameObject
- ``EventHistory``: TRacks the history of this residence
- ``Building``: Describes the building the residence is in


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

    Businesses:
        - name: "House"
          # Other data fields ...
        - name: "Mansion"
          # ...
        - name: "Shack"
          # ...