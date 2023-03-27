Characters
==========

Characters are our agents. They interact with each other, form relationships, engage
in life, events, have children, and work jobs. One of the goals of this project was
to make the character authoring process more flexible than that offered by
*Talk of the Town*.

Character components
--------------------

Characters like other GameObjects are a collection of components. Some components are
required for characters to function properly. The following is a list of components
currently used to drive characters

- ``GameCharacter``: Defines the first and last name of the character using Tracery
  grammars
- ``Age``: Defines the age of the character
- ``AgingConfig``: Defines the ages that characters change life stages. This is similar
  to the aging system in *The Sims* where characters can start as children and grow to
  adulthood
- ``Lifespan``: Defines how long a character lives on average
- ``MarriageConfig``: Defines parameters for what spouse a character can be generated
  with.
- ``ReproductionConfig``: Defines how many children a character can have at spawn and
  what prefabs the children are allow to be instances of
- ``RelationshipManager``: (always empty) Ensures characters can track relationships
- ``Virtues``: An interpretation of character personality based on what virtues they
  vakue in life
- ``CanAge``: This marks a character as being eligibile to grow older.
- ``StatusManager``: Tracks all instances of StatusComponents attached to the character
- ``TraitManager``: Tracks all instances of TraitComponents attached to the character
- ``EventHistory``: Tracks all the life events this character has been a part of
- ``AIBrain``: Manages decision-making for characters
- ``FrequentedLocations``: Tracks what locations character frequent based on their
  characteristics, residence, and current occupation.

Defining a character prefab
---------------------------

We construct characters using *CharacterPrefabs*. These prefabs are defined using YAML
files and loaded into the simulation using  utility functions.

All characters should have atleast one ``GameCharacter`` entry under their
``components`` specification. That is how we know that they are a character and not a
business or residential building.

Along with component data, CharacterPrefabs also have fields for:

- ``Spawn Frequency``: The relative frequency of this character prefab in the
  simulation, compared to other character prefabs (defaults to 1).
- ``extends``: (Optional) The name of the Character prefab that this one extends
- ``tags``: (Optional) String tags for filtering

Below is an example of a character prefab in YAML. We start by defining the name of the
prefab. Then specify if it is a template and its spawn_frequency. Finally, we create
a map named ``components`` and add entries for each component type that should be
attached to instances of this prefab at creation time. Each component in this prefab
should have been registered with the ECS. Components whose factories do not accept
arguments are specified with a ``{ }`` indicating an empty object. All the components
listed in the sample below are required for characters to function properly. So, when
creating new character prefabs, it is best to just extend the ``character::default``
prefab. It will save you time.

.. code-block:: yaml

    name: character::default
    is_template: yes
    spawn_frequency: 1
    components:
        GameCharacter:
            first_name: "#character::default::first_name::gender-neutral#"
            last_name: "#character::default::last_name#"
        AgingConfig:
            adolescent_age: 13
            young_adult_age: 18
            adult_age: 30
            senior_age: 65
        Lifespan:
            value: 85
        MarriageConfig:
            spouse_prefabs:
            - "character::default::.*"
            chance_spawn_with_spouse: 0.5
        ReproductionConfig:
            max_children_at_spawn: 3
            child_prefabs:
            - "character::default::.*"
        RelationshipManager: { }
        Virtues: { }
        CanAge: { }
        StatusManager: { }
        TraitManager: { }
        FrequentedLocations: { }
        AIBrain: { }
        Goals: { }
        EventHistory: { }
        Age: { }

Loading the prefab
------------------

You can add your prefab to the simulation using loader functions included with
Neighborly.

1. ``load_character_prefab(sim.world, "path/to/yaml/file")``
2. ``load_data_file(sim.world, "path/to/yaml/file")``

There is a slight difference between these two functions. The first is intended to load
a single character prefab from a file. That is what we would use for the example
definition above. However, if we placed multiple character prefabs in the same file,
the second function would load them all at once. The only change we would need to make
the second option work is to place our definitions within a YAML list (see below).
You can alays reference the included plugin code to get a better understanding of how
to use these functions.

.. code-block:: yaml

    Characters:
        - name: "SampleCharacter"
          # Other data fields ...
        - name: "SampleCharacterVariation"
          # ...
        - name: "Android"
          # ...
