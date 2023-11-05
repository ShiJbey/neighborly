.. _residences:

Residential Buildings
=====================

While Neighborly, does not model characters exact locations, we do model where they live. This is an important part of defining who a character is. There is a big difference in a character living within a small apartment in the slums versus a character living in a fancy penthouse apartment in the "Affluent" district.

Residential buildings control the max population size of a settlement as new characters only spawn when there is available space to live. Each residential building has one or more residential units. You can think of a residential unit a slot where an individual or family might live. Houses have one residential unit, as they usually only house one family, while apartment buildings have multiple units because they are multifamily housing.

As with other content, residence definitions should be done in a JSON file(s). Below are a few examples of residential building definitions.

Defining new residential building types
---------------------------------------

- ``display_name``: A regular text name of the residential building.
- ``residential_units``: The number of units within the building.
- ``spawn_frequency``: (A whole number) Relative frequency of this residence building type spawning relative to other residence definitions.

.. code-block:: json

    {
        "house": {
            "display_name": "House",
            "residential_units": 1,
            "spawn_frequency": 3
        },
        "mansion": {
            "display_name": "Mansion",
            "residential_units": 1,
            "spawn_frequency": 1
        },
        "small_apartment_building": {
            "display_name": "Small Apartment Building",
            "residential_units": 4,
            "spawn_frequency": 3,
            "required_population": 0
        },
        "medium_apartment_building": {
            "display_name": "Medium Apartment Building",
            "residential_units": 6,
            "spawn_frequency": 1,
            "required_population": 20
        },
        "large_apartment_building": {
            "display_name": "Large Apartment Building",
            "residential_units": 10,
            "spawn_frequency": 1,
            "required_population": 30
        }
    }


Loading definitions
-------------------

Neighborly provides the ``neighborly.loaders.load_residences(sim, "path/to/file")`` function to help users load their residential building definitions fom JSON. This function handles reading in the data and registering it with the internal libraries.

.. code-block:: python

    from neighborly.simulation import Simulation
    from neighborly.loaders import load_residences

    sim = Simulation()

    load_residences(sim, "path/to/file")
