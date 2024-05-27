.. _relationships:

Relationships
=============

.. attention:: This page needs to be updated for version 3

Relationships track how characters feel about each other. They track directed stats that represent the feelings of the owner of the relationship toward the target of the relationship. In this way, characters may have asymmetric relationships. For instance, one character having a high reputation value of the other, but the feelings not being reciprocated.

Relationships are represented as GameObjects with two required components ``Relationship``, ``Traits``, and ``Stats``. The ``Relationship`` component tracks the owner and target of the relationship, the ``Traits`` component tracks all traits applied to the relationship, and the ``Stats`` component tracks stats related to the relationship.

Relationship stats
------------------

The following are the stats used to represent relationships:

- ``romance``: (-100 to 100) A measure of the owner's romantic affinity toward the target.
- ``reputation``: (-100 to 100) A measure of the owner's general (or platonic) affinity toward the target.
- ``romantic_compatibility``: (-100 to 100) A measure of how strongly romantic feelings will passively grow or decrease over time.
- ``compatibility``: (-100 to 100) A measure of how strongly the reputation state will passively grow or decrease over time.
- ``interaction_score``: (0 to 10)A measure of how often characters interact during a year. This affects the strength of the passive growth/decline of the romance and reputation stats.

Working with stats in Python
----------------------------

The following is an example of how to create new relationships between characters, manually modify stats, and apply traits to the relationship.

.. code-block:: python

    from neighborly.simulation import Simulation
    from neighborly.helpers.traits import add_trait, has_trait, remove_trait
    from neighborly.helpers.relationships import get_relationship
    from neighborly.loaders import load_traits, load_characters

    sim = Simulation()

    # Load trait and character definition data
    load_traits(sim, "path/to/file")
    load_characters(sim, "path/to/file")

    # Traits are initialized at the start of the simulation
    sim.initialize()

    chris = create_character(sim.world, "person")
    sam = create_character(sim.world, "person")

    # Adds two traits to the relationship from Chris to Sam
    # The get_relationship(...) function creates a new relationship
    # if one does not already exist.
    add_trait(get_relationship(chris, sam), "friends")
    add_trait(get_relationship(chris, sam), "rivals")

    # Adds two traits to the relationship from Sam to Chris
    add_trait(get_relationship(sam, chris), "friends")
    add_trait(get_relationship(sam, chris), "rivals")

    # Reduce the base value of the romance stat by 25
    get_stat(get_relationship(sam, chris), "romance").base_value -= 25

Social Rules
------------

Social rules modify how characters feel about each other. They help to make a more socially interesting simulation. Social rules are mostly associated with traits and can be added using the ``AddSocialRule`` Effect. For example, you can have a ``prejudice-against-elves`` trait that, when attached to a character, would add a social rule that decreases the base reputation of that character toward all characters with the 'elf' trait. Social rules allow us to build very complicated relationships between characters using constructs that are quite simple to create and modify.

Adding a social rule to a character will affect pre-existing and future relationships. When a social rule is removed, all relationships are recalculated.

The structure of a social rule
------------------------------

Social rules have three pieces: ``preconditions``, ``effects``, and a ``source``. The preconditions are callable objects or functions that accept a relationship GameObject as a parameter and return True if the relationship meets their conditions. The effects are Effect objects applied to the relationship if all the preconditions pass. These Effects have the same structure as those associated with traits, except they are provided a relationship as the target object to modify. Finally, the source tracks what was responsible for constructing the social rule and adding it to the character's ``SocialRules`` component. We use the source reference to track which social rules are associated with which traits.

Defining social rules
---------------------

Currently, all social rules are authored within traits using the ``AddSocialRule`` effect. Perhaps a later feature could be authoring global social rules that are applied to all characters regardless of their associated traits. Below is an example definition of our elf prejudice trait. With this trait attached, all relationships this character has with character with the ``elf`` trait will receive an automatic reputation penalty of -10.

.. code-block:: json

    {
        "prejudice_against_elves": {
            "display_name": "Prejudice against elves",
            "description": "This character does not like elves",
            "effects": [
                {
                    "type": "AddSocialRule",
                    "preconditions": [
                        {
                            "type": "HasTrait",
                            "trait": "elf"
                        }
                    ],
                    "effects": [
                        {
                            "type": "StatBuff",
                            "stat": "reputation",
                            "amount": -10
                        }
                    ]
                }
            ]
        }
    }
