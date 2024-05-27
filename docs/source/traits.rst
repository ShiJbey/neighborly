.. _traits:

Traits
======

.. attention:: This page needs to be updated for version 3


Traits are tags that can be applied to entities like characters, relationships, and businesses. Traits can represent personality traits, faction memberships, and relationship types/statuses ("coworker", "dating", "secret-lover", ...). Their greatest strength is that users can specify effects that are triggered when the trait is added to a GameObject. Effects can range from stat/skill buffs to location preferences to social rules. When a trait is added to an object, all the effects are immediately applied. And when a trait is removed, all the effects are also undone. For example, a ``friendly`` trait might boost a character's ``sociability`` stat and provide a ``reputation`` boost on all relationships. When the trait is added, that character will immediately get the stat buff and a boost on all their active relationships. And when the trait is removed, they will lose their ``sociability`` boost, and all relationships will lose the ``reputation`` boost.

If you are interested in learning how to create custom effect types and make them available for content authoring, please see the :ref:`effects_preconditions` page.

Defining new traits
-------------------

Users should define all traits within a JSON file(s). All traits can be specified within the same file. Please remember that if you specify a spawn_frequency, characters may spawn with that trait. If the trait is not meant for characters, this may result in runtime issues. Trait definitions have the following optional fields:

- ``display_name``: (str) A one to two-word name for displaying in text. (default is the trait ID)
- ``description``: (str) A short text description of the trait. (default is "")
- ``effects``: (list[dict[str, Any]]) A list of effect objects data. (default is [])
- ``conflicts_with``: (list[str]) A list of IDs of traits this trait cannot coexist with on the same object. (default is [])
- ``spawn_frequency``: (float) (For character traits) The relative frequency of a character being gaining the trait when generated. (default is 0)
- ``inheritance_chance_single``: (float) The probability of a character inheriting this trait if one parent has it. (default is 0)
- ``inheritance_chance_both``: (float) The probability of a character inheriting this trait if both parents have it. (default is 0)

Below is an example of a ``Gullible`` trait. As with other definition types, we start with a unique trait ID followed by a colon. All attributes for the trait are then specified below it. Notice that it has two effects specified for when this trait is added. Each effect starts with a ``type`` key that specifies the effect type, followed by additional key-value pair parameters to use when constructing the effect object. Here we have a sociability buff and a social rule. There are buff effects for all character and relationship stats. The ``AddSocialRule`` effect is special because it is how traits change a character's feelings toward other characters. Here we have a social rule that boosts the gullible character's outgoing reputation scores. See the Social Rules section of the :ref:`relationships` page for more information about social rules. Finally, we specify that it conflict with the trait that has the ID, skeptical, as well as stats for giving character's this trait at spawn.

.. code-block:: json

    {
        "gullible": {
            "display_name": "Gullible",
            "description": "This character is more trusting of others to a fault.",
            "effects": [
                {
                    "type": "StatBuff",
                    "stat": "sociability",
                    "amount": 3
                },
                {
                    "type": "AddSocialRule",
                    "effects": [
                        {
                            "type": "StatBuff",
                            "stat": "reputation",
                            "amount": 5
                        }
                    ]
                }
            ],
            "conflicts_with": [ "skeptical" ],
            "spawn_frequency": 1,
            "inheritance_chance_single": 0.25,
            "inheritance_chance_both": 0.5
        }
    }

Below is an example of the same trait defined using YAML

.. code-block:: yaml

    gullible:
        display_name: Gullible
        description: This character is more trusting of others to a fault.
        effects:
            - type: StatBuff
              stat: Sociability
              amount: 3
            - type: AddSocialRule
              stat: reputation
              amount: 5
        conflicts_with:
            - skeptical
        spawn_frequency: 1
        inheritance_chance_single: 0.25
        inheritance_chance_both: 0.5

Last, we have an example of a trait defined directly in Python.

.. code-block:: python

    gullible = DefaultTraitDef(
        definition_id="gullible",

    )




Loading traits into the simulation
----------------------------------

Neighborly supplies users with loaders for various types of data. JSON files should contain all of one type of data. In this case, trait files should only contain trait definitions. Users can load their trait definitions into the simulation using the following function

.. code-block:: python

    from neighborly.simulation import Simulation
    from neighborly.loaders import load_traits

    sim = Simulation()

    load_traits(sim, "path/to/file")



Using traits from Python
------------------------

Neighborly has a few helper functions to help users interface with traits from Python -- `add_trait`, `has_trait`, and `remove_trait`. The helper functions are located in the `neighborly.helpers.traits` module. Users should use these functions instead of interfacing directly with the `Traits` component that is attached to all characters, relationships, and businesses. Each function accepts the GameObject to modify and the definition ID of the trait.

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

    chris = create_character(sim.world, "farmer")

    # Add a trait to Chris with the ID "flirtatious"
    add_trait(chris, "flirtatious")

    # Create another character
    sam = create_character(sim.world, "farmer")

    # Adds two traits to the relationship from Chris to Sam
    add_trait(get_relationship(chris, sam), "friends")
    add_trait(get_relationship(chris, sam), "rivals")

    # Adds two traits to the relationship from Sam to Chris
    add_trait(get_relationship(sam, chris), "friends")
    add_trait(get_relationship(sam, chris), "rivals")

    # Chris is no longer flirtatious and any effects of the trait are removed
    remove_trait(chris, "flirtatious")
