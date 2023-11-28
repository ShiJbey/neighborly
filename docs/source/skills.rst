.. _skills:

Skills
======

Neighborly uses skills to track each character's proficiency levels for various tasks such as cooking, swordsmanship, seduction, marksmanship, water magic, explosion magic, and salesmanship. Skills provide an alternative an alternative method of representing character stats. Every skill has a value in the range ``0`` to ``255``, with ``255`` meaning that a character has maxed out that skill.

Characters can be given skills when generated, and they can acquire skills from various jobs. Skills are mainly used as preconditions for characters qualifying for specific job roles at businesses within the settlement. The :ref:`businesses` wiki page explains how to perform skill checks as preconditions for job roles. Skills may also be used as event probability considerations or buffs when calculating the probability of success when performing a behavior.

How are skills represented?
---------------------------

At runtime, skills are represented as individual GameObjects with one :py:class:`~neighborly.components.skills.Skill` component containing basic metadata (name and description). Each character's specific skills are managed by their :py:class:`~neighborly.components.skills.Skills` (note the plural 's') component that contains a map of skill GameObjects to :py:class:`~neighborly.components.stats.Stat` instances that track the level of the skills.

Specifying skill data
---------------------

Users specify new skills in data (JSON or YAML) files. Below are examples of a few skills. Each definition starts with a definition ID that is unique to this skill. Each definition has two optional attributes, the ``display_name`` and ``description``. The display name is a regular English name given to the skill. Unlike the definition IDs, display names do not need to be unique. While it may be confusing, multiple skill definitions can have the same display name. The description is a short text blurb about what the skill represents. They help when generating prose descriptions of characters and their skills.

Naming conventions for definition IDs:

- Do not use spaces. Use underscores or dashes
- IDs should be all lowercase letters

Defining skills in JSON:

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

Defining skills in YAML:

.. code-block:: yaml

    cooking:
        display_name: Cooking
        description: A measure of how good a character is at cooking delicious food.

    swordsmanship:
        display_name: Swordsmanship
        description: A measure of how well a character can handle a sword.

    explosion_magic:
        display_name: Explosion Magic
        description: A measure of how proficient a character is at using explosion magic.

Defining skills directly in Python:

Users can define skills using Python dicts or directly using definition classes.

.. code-block:: python

    skill_lib = sim.world.resource_manager.get_resource(SkillLibrary)

    # Option 1: This uses a specific class to construct the definition

    cooking = DefaultSkillDef(
        definition_id="cooking",
        display_name="Cooking",
        description="A measure of how good a character is at cooking delicious food."
    )

    skill_lib.add_definition(cooking)

    # Option 2: This uses a data dict and lets the library choose what definition class
    # to use when constructing the definition. This is how data is loaded from data files

    swordsmanship = {
        "definition_id": "Swordsmanship"
        "display_name": "Swordsmanship",
        "description": "A measure of how well a character can handle a sword."
    }

    skill_lib.add_definition_from_obj(swordsmanship)


Using skills from Python
------------------------

Skills are tracked in :py:class:`~neighborly.components.skills.Skills` components attached to characters. Most of the time, if you're writing Python code to modify skills, you will want to avoid changing this component directly. Instead, you will want to interface with them using the provided helper function(s) in the :py:mod:`neighborly.helpers.skills` module. Below is an example of adding, retrieving, and modifying skills.

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

Advanced: Creating custom skill definition classes
--------------------------------------------------

Users who want to add fields to the skill definitions or change how skill definitions are instantiated will need to define new :py:class:`~neighborly.defs.base_types.SkillDef` subclasses. This might be the case if you want to use a custom text generator to create skill descriptions and names. By default, Neighborly uses the :py:class:`~neighborly.defs.defaults.DefaultSkillDef` class to store skill definitions that are loaded from external data files or definitions loaded directly into the :py:class:`~neighborly.libraries.SkillLibrary` using the :py:meth:`~neighborly.libraries.SkillLibrary.add_definition_from_obj` method. Users can supply new definition classes in Python and set a specific definition class as the default when loading new skill definition data.

Note the following terms:

- "definition data": the parameters passed to a definition class
- "definition": an instance of a definition class (constructed in Python)
- "definition type/class": the Python class definition used to create instances of definitions

Step 1: Create a new ``SkillDef`` subclass
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The first step is creating a new class that inherits directly or indirectly from :py:class:`~neighborly.defs.base_types.SkillDef`. For this example, we will inherit from :py:class:`~neighborly.defs.defaults.DefaultSkillDef`. All skill definition classes need to override the following two abstract methods:

- :py:meth:`neighborly.defs.base_types.SkillDef.from_obj`
- :py:meth:`neighborly.defs.base_types.SkillDef.initialize`

Below, we have Python pseudocode for defining a new definition class called ``CustomSkillDef``. Users can add new class instance variables directly in the function body. Skill definitions are Python data classes created using `attrs <https://www.attrs.org/en/stable/index.html>`_. Here, we add a string variable for a large language model for name/description generation.

.. code-block:: python

    class CustomSkillDef(SkillDef):
        """A custom skill definition that uses an LLM to generate names and descriptions."""

        llm_model_name: str
        """The name of the LLM to use for text generation."""

        @classmethod
        def from_obj(cls, obj: dict[str, Any]) -> SkillDef:
            definition_id = obj["definition_id"]
            display_name = obj.get("display_name", definition_id)
            description = obj.get("description", "")

            # The code below gets the llm_model_name from the dict or
            # an empty string if none is provided
            model_name = obj.get("llm_model", "")

            return cls(
                definition_id=definition_id,
                display_name=display_name,
                description=description,
            )

        def initialize(self, skill: GameObject) -> None:
            if self.llm_model_name == "gpt4":
                skill_name = ... # Do GPT-4 stuff
                description = ... # Do GPT-4 stuff
            if self.llm_model_name == "gpt3":
                skill_name = ... # Do GPT-3 stuff
                description = ... # Do GPT-3 stuff
            else:
                # Default to tracery
                tracery = skill.world.resource_manager.get_resource(Tracery)

                skill_name = tracery.generate(self.display_name)
                description = tracery.generate(self.description)

            skill.add_component(
                Skill(
                    definition_id=self.definition_id,
                    display_name=skill_name,
                    description=description,
                )
            )

Step 2: Add the definition class to the library
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The next step before we can use this custom definition is to add it to the :py:class:`~neighborly.libraries.SkillLibrary` using :py:meth:`~neighborly.libraries.SkillLibrary.add_definition_type`. This method makes the definition available when loading data from data files. It allows users to override the default definition class used to load definition data.

The following code should be placed inside a plugin's ``load_plugin()`` function. However, it can be placed anywhere after the simulation has been instantiated and **before** any content is loaded from external files.

.. code-block:: python

    skill_lib = sim.world.resource_manager.get_resource(SkillLibrary)

    skill_lib.add_definition_type(
        CustomSkillDef, alias="custom", set_default=True
    )

Step 3: Use the definition from within a data file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following shows how to use the custom definition type within a YAML data file. Notice that the definition supplies the ``definition_type`` attribute. This tells Neighborly to load this definition data using the definition type saved to the given alias name. If ``definition_type`` is not given, Neighborly will default to the last definition type added to the library with ``set_default=True``.

.. code-block:: yaml

    gift_of_gab:
        definition_type: custom
        llm_model: gpt4
        display_name: Gift of Gab
        # put an LLM prompt below to pass to GPT-4
        description: >-
            Generate a description of a "Gift of Gab" skill
