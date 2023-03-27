Businesses
==========

Businesses are locations within the town that house places where people work. They add
an additional layer of narrative richness to the simulation by fleshing out the type
of settlement that characters live in. Meeting and interacting with people at work is
one of the main ways that relationships grow. Characters spend a good amount of time in
close social proximity with their coworkers.

Business components
--------------------

Businesses like other GameObjects are a collection of components. Some components are
required for businesses to function properly. The following is a list of components
currently used to drive businesses

- ``Name``: Defines the name of the business using Tracery a grammar
- ``Lifespan``: Defines how long a business lives on average
- ``StatusManager``: Tracks all instances of StatusComponents attached to the business
- ``EventHistory``: Tracks all the life events this business has been a part of
- ``Business``: Defines business-specific information
- ``Location``: Marks the business as a place that characters can travel to
- ``Activities``: (Optional) things characters can do at a location
- ``FrequentedBy``: Tracks characters that frequent this locaiton
- ``Building``: Describes the building the business is within

Defining a business prefab
---------------------------

We construct businesses using *BusinessPrefabs*. These prefabs are defined using YAML 
files and loaded into the simulation using  utility functions.

All businesses should have atleast one ``Business`` entry under their 
``components`` specification. That is how we know that they are a business and not a
character or residential building. 

Along with component data, BusinessPrefabs also have fields for:

- ``Spawn Frequency``: The relative frequency of this business prefab in the
  simulation, compared to other business prefabs (defaults to 1).
- ``extends``: (Optional) The name of the Character prefab that this one extends
- ``tags``: (Optional) String tags for filtering
- ``max_instances``: Limits the number of instances of this prefab in a settlement
- ``min_population``: Requires that a certain population size be reached in a settlement
  before this prefab will spawn
- ``year_available``: Time locks the business prefab to only spawn after the simulation
  has reached a specified year
- ``year_obsolete``: Time locks businesses with a year that they will nolonger spawn in
  the simulation

Below is an example of a business prefab in YAML. We start by defining the name of the
prefab. Then specify if it is a template and its spawn_frequency. Finally, we create
a map named ``components`` and add entries for each component type that should be
attached to instances of this prefab at creation time. Each component in this prefab
should have been registered with the ECS. Components whose factories do not accept
arguments are specified with a ``{ }`` indicating an empty object. All the components
listed in the sample below are required for businesss to function properly. So, when
creating new business prefabs, it is best to just extend the ``business::default``
prefab. It will save you time.

.. code-block:: yaml

    name: business::default
    is_template: true
    spawn_frequency: int = 1
    max_instances: int = 9999
    min_population: int = 0
    year_available: int = 0
    year_obsolete: int = 9999
    components:
        Name:
            value: "Business"
        Business: { }
        StatusManager: { }
        Location: { }
        Activities: { }
        FrequentedBy: { }
        EventHistory: { }
        Building:
            building_type: commercial
        Lifespan:
            value: 10


Loading the prefab
------------------

You can add your prefab to the simulation using loader functions included with 
Neighborly.

1. ``load_business_prefab(sim.world, "path/to/yaml/file")``
2. ``load_data_file(sim.world, "path/to/yaml/file")``

There is a slight difference between these two functions. The first is intended to load
a single business prefab from a file. That is what we would use for the example 
definition above. However, if we placed multiple business prefabs in the same file, 
the second function would load them all at once. The only change we would need to make
the second option work is to place our definitions within a YAML list (see below).
You can alays reference the included plugin code to get a better understanding of how
to use these functions.

.. code-block:: yaml

    Businesses:
        - name: "SampleBusiness"
          # Other data fields ...
        - name: "SampleBusinessVariation"
          # ...
        - name: "WacArnold's Restaurant"
          # ...


Services
--------

Services are things that the business offers customers. They may be used to cast
businesses into roles within events that require a particular business. For example,
a `ChildBirthEvent` may choose a to record a hospital where the child was born. To do
this we could search for all game objects with a ``Services`` component then filter for
``Services`` containing the *"hospital"* service. You can easily do this using the
``find_places_with_services(world, *services)`` utility function.

.. code-block:: python

    hospitals = find_places_with_services(world, "hospital")
    print(hospitals)

At this point you may be wondering how you add services to a business. This is done
within the entity prefab file. Add a "Services" entry under the *components* map and
enter the list of services. These are case-insensitive, but typos and misspellings are
not caught by the system. So, be sure to be consistent in your naming conventions.
Please note that the "Service" entry (capital *S*) has a keyword argument "service"
(lowercase *s*).

.. code-block:: yaml

    name: "business::hospital"
    extends: "business::default"
    config:
        owner_type: Doctor
    components:
        Business:
            name: "Hospital"
            employees:
                Doctor: 2
                Nurse: 3
                Secretary: 1
        # Services go here!!
        Services:
            services:
                - hospital
                - emergency_medical
