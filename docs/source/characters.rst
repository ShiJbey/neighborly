.. _characters:

Characters
==========

.. attention:: This page needs to be updated for version 3

Characters inhabit the settlement, own businesses, interact, and generate events that we will later mine for emergent stories. Character definitions are specifications for what types of characters can spawn within a district. They do not represent any one particular character, but rather a class of characters. For example, a ``person`` definition might create generic human characters with a subset of randomly selected traits, while an ``blacksmith`` definition might create similar character and give them a bonus Blacksmithing skill at spawn.

Each timestep there is a chance that a new character will spawn into a vacant residential unit in the settlement. By default, characters always spawn in as single adult-aged individuals and **not** as families. This simplifies the process that's required to make families look believable.

Characters have the following default components that manage their internal data. Custom character implementations should ensure that these components are present when instantiating Character GameObjects.

- ``Character``: Character demographic data such as their first name, last name, age, sex, and species.
- ``Traits``: A collection of traits attached to the character.
- ``Skills``: A mapping of Skills to skill level stats.
- ``Stats``: A mapping of stat ID's to Stat instances.
- ``FrequentedLocations``: A collection of locations that this character frequents.
- ``Relationships``: Manages references to all the relationship instances for how this character feels about others and how others feel about this character.
- ``LocationPreferences``: A collection of rules that determine what locations a character is most likely to frequent during a month.
- ``SocialRules``: A collection of social rules that affect a character's relationship's stats.
- ``PersonalEventHistory``: Stores a list of all the life events that have directly involved this characters.

Sexes
-----

Every character has a biological sex that is stored within their ``Character`` components. A character's sex may be ``MALE``, ``FEMALE``, or ``NOT_SPECIFIED``. We represent it this way to simplify reproduction calculations.

Life stages
-----------

As characters get older, they can age physically. Characters have the following life stages they can progress through: ``CHILD``, ``ADOLESCENT``, ``YOUNG_ADULT``, ``ADULT``, and ``SENIOR``. The ages at which character reach these life stages varies based on the character's species. Events and systems can use a character's life stage to determine when and if character's should engage in certain behaviors.

Species
-------

Each character has a species that defines parameters for their biological processes. For example, it handles aging parameters for when characters change life stages and character lifespans.

Species are specified as a subtype of ``Trait``. This means that species can take advantage of all the same ``Effects`` that normal traits do. Species should be defined within JSON files containing other trait or species definitions. So that the system recognizes the traits as species, add a ``"definition_type": "species"`` attribute to the definition. This will tell the ``TraitLibrary`` to load the definition as a new species.

The example below shows a definition for a ``human`` species.

.. code-block:: json

    {
        "human": {
            "definition_type": "species",
            "display_name": "Human",
            "description": "A plain ol' human being.",
            "adolescent_age": 13,
            "young_adult_age": 20,
            "adult_age": 30,
            "senior_age": 65,
            "lifespan": 80,
        }
    }

Character stats
---------------

Character have the following stats by default:

- ``boldness``: How bold is a character, [0, 255]
- ``stewardship``: A measure of their capabilities for organization and leadership, [0, 255]
- ``sociability``: A character's tendency toward social behavior, [0, 255]
- ``attractiveness``: A measure of a character's aesthetic attractiveness [0, 255]
- ``intelligence``: A measure of a character's education or intellect
- ``reliability``: How reliable is a character [0, 255]
- ``fertility``: The probability of a character being able to conceive a child. [0.0, 1.0]
- ``health``: How far is a character from death. [0, inf]
- ``health_decay``: The amount of health lost each year the character is alive. [-100, 100]

Defining new character types
----------------------------

Users should define new character types within JSON data file that contain other character definitions. These definitions can be loaded into a simulation using the ``load_characters(sim, "path/to/file")`` function provided by the ``neighborly.loaders`` module.

Default character definition parameters
---------------------------------------

- ``spawn_frequency``: The frequency of spawning relative to others in the district. (Defaults to 1)
- ``species``: IDs of species to choose from and assign to the character. (Defaults to [])
- ``max_traits``: The max number of random traits this character type spawns with. (Defaults to 5)
- ``default_traits``: List of trait IDs of trait automatically applied to the character during generation. (Defaults to [])
- ``default_skills``:  Key value pairs of trait IDs mapped to strings containing min-max interval values for skills.

Character definitions specify parameters for creating new instances of characters.

.. code-block:: json

    {
        "person": {
            "spawn_frequency": 1,
            "species": [
                "human"
            ],
            "gender": [
                "Male",
                "Female"
            ],
            "max_traits": 3
        },
        "farmer": {
            "spawn_frequency": 1,
            "species": [
                "human"
            ],
            "gender": [
                "Male",
                "Female"
            ],
            "max_traits": 3,
            "skills": {
                "farming": "20 - 230"
            }
        }
    }

How do characters get traits?
-----------------------------

All traits that have a spawn_frequency greater than zero are considered for selection when generating a new character. The default is to select a max of 3 eligible traits. This all happens within a call to ``create_character(world, "definition_id")``. If you want to change the max number of spawned traits, add the `n_traits` keyword argument to the ``create_character`` function call. The following code would create a new character using the "aristocrat" definition with a maximum of 8 traits.

.. code-block:: python

    create_character(sim.world, "aristocrat", n_traits=8)


Reproduction
------------

Female characters have a chance to get pregnant while in romantic relationships with a male character. This depends on their fertility values. By default, a couple's chance to conceive is the average of their fertility scores.

When a character becomes pregnant, they will gain a ``Pregnant`` component that contains a reference to other parent of the conceived child, and the date the child will be born. After nine months of simulation time, a new child is spawned into the simulation. Its attributes are a mix of the parents.
