.. _skills:

Skills
======

Neighborly tracks characters' proficiency levels for various skills. Every skill has a value on the range 0 to 255, with 255 meaning that a character has maxed-out that skill. skills can be things like cooking, swordsmanship, marksmanship, water magic, explosion magic, flirting, etc.

Characters can be given skills when they are generated, and they can acquire skills from working various jobs. Skills are mainly used as a precondition for characters qualifying for certain job roles at businesses within the settlement. The :ref:`businesses` wiki page explains how to perform skill checks as preconditions for job roles. Skills may also be used as event probability considerations or buffs when calculating the probability of success when performing a behavior.

How are skills represented?
---------------------------

At runtime, skills are represented in two places. First, all Skills are instantiated as individual GameObjects containing ``Skill`` components. Next characters are given ``Skills`` components that internally map skills to a ``Stat`` instance that tracks the level of the skill.

Specifying skill types
----------------------

Users specify new skills in JSON files. Below are examples of a few skills. Each definition starts with a definition ID that is unique to this skill. Each definition has two optional attributes, the ``display_name`` and ``description``. The display name is a regular English name given to the skill. Unlike the definition IDs, display names do not need to be unique. While it may be confusing, multiple skill definitions can have the same display name. The description is a short text blurb about what the skill represents. They help when generating prose descriptions of characters and their skills.

.. code-block:: json

    {
        "cooking": {
            "display_name": "Cooking",
            "description": "A measure of how good a character is at cooking delicious food."
        },
        "swordsmanship": {
            "display_name": "Swordsmanship",
            "description": "A measure of how well a character can handle a sword."
        },
        "explosion_magic": {
            "display_name": "Explosion Magic",
            "description": "A measure of how proficient a character is at using explosion magic."
        }
    }


Using skills from Python
------------------------

Skills are tracked in ``Skills`` components attached to characters. Most of the time, if you're writing Python code to modify skills, you will not want to modify this component directly. Instead, you will want to interface with them using the provided helper function(s) in the ``Neighborly.helpers.skills`` module. Below is an example of adding, retrieving, and modifying skills.

.. code-block:: python

    from neighborly.simulation import Simulation
    from neighborly.loaders import load_characters, load_skills
    from neighborly.helpers.character import create_character
    from neighborly.helpers.skills import get_skill
    from neighborly.components.stats import StatModifier, StatModifierType


    sim = Simulation()

    # Load authored data for generating characters and skills
    load_characters(sim, "path/to/file")
    load_skills(sim, "path/to/file")

    # Instantiate the simulation to process loaded skill definitions
    sim.instantiate()

    # Create a new character
    character = create_character(sim.world, "person")

    # Add a cooking skill to the character
    add_skill(character, "cooking", 0)

    # Get a character's skill
    cooking_skill = get_skill(character, "cooking")

    # Change the base value
    cooking_skill.base_value += 1

    # Add stat modifiers
    cooking_skill.add_modifier(
        StatModifier(
            modifier_type=StatModifierType.Flat,
            value=25,
        )
    )

    # Print the final calculated value
    print(cooking_skill.value)
    #    26
