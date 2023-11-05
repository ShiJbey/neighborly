.. _effects_preconditions:

Effects and Preconditions
=========================

``Effects`` are a class of objects that can perform modifications to a GameObject when applied and undo their modifications when removed. Effects are used with traits and social rules to make changes to characters and relationships.

``Preconditions`` are a class of objects that check GameObjects for certain conditions. If these conditions are met, they return true.

Using effects and preconditions
-------------------------------

Effects are specified within the ``effects`` section of traits. Each effect ``type`` is internally mapped to a class type of the same name that inherits from Neighborly's ``Effect`` base class. Within the key-value pair specification, all other key-value pairs aside from the ``type`` key are passed to a function that constructs a new instance of that effect type.

The example below shows a trait with multiple effects. All effects are applied when a trait is attached. One of the effects adds a new location preference rule that accepts a list of preconditions. Like effects, precondition specifications require the user to provide a `type: ...`, and all other key-value pairs are used to parameterize an instance of that precondition type. Here we specify that this location preference only applies to places that serve alcohol.

.. code-block:: json

    {
        "drinks_too_much": {
            "display_name": "Drinks too much",
            "effects": [
            {
                "type": "StatBuff",
                "stat": "health_decay",
                "amount": 0.05,
                "modifier_type": "FLAT"
            },
            {
                "type": "AddLocationPreference",
                "preconditions": [
                {
                    "type": "HasTrait",
                    "trait": "serves_alcohol"
                }
                ],
                "amount": 0.2
            }
            ]
        }
    }


Built-in effects
----------------

Below are a list of all the currently built-in effect types. If users want to add more, they can create a new subclass of ``Effect`` and register their effect type using.

.. code-block:: python

    sim.world.resource_manager.get_resource(EffectLibrary).add_effect_type(CustomEffect)


- ``StatBuff``: Adds a modifier to a relationship's interaction_score stat

  - Parameters:

    - ``stat``: the ID of the stat to buff
    - ``modifier_type``: "FLAT", "PERCENT_ADD", or "PERCENT_MULTIPLY"
    - ``amount``: number

- ``IncreaseSkill``: Permanently increases a skill stat

  - Parameters:

    - ``skill_name``: str
    - ``amount``: number

- ``AddLocationPreference``: Adds a location preference rule to the character

  - Parameters:

    - ``preconditions``: list of preconditions
    - ``modifier_type``: "Flat", "PercentAdd", or "PercentMult"
    - ``amount``: number

- ``AddSocialRule``: Adds a social rule to the character

  - Parameters:

    - ``preconditions``: list of preconditions
    - ``effects``: list of effects

Defining new effects
--------------------

users can create new event types that can be access from JSON definitions. First, you need to create a new class that inherits from the ``Effect`` class and then register that effect by adding it to the library. See the example code below for the ``StatBuff`` effect.

.. code-block:: python

    class StatBuff(Effect):
        """Add a buff to a stat."""

        __slots__ = "modifier_type", "amount", "stat_id"

        modifier_type: StatModifierType
        """The how the modifier amount should be applied to the stat."""
        amount: float
        """The amount of buff to apply to the stat."""
        stat_id: str
        """The definition ID of the stat to modify."""

        def __init__(
            self,
            stat_id: str,
            amount: float,
            modifier_type: StatModifierType,
        ) -> None:
            super().__init__()
            self.stat_id = stat_id
            self.modifier_type = modifier_type
            self.amount = amount

        @property
        def description(self) -> str:
            return (
                f"add {self.amount}({self.modifier_type.name}) modifier to {self.stat_id}"
            )

        def apply(self, target: GameObject) -> None:
            get_stat(target, self.stat_id).add_modifier(
                StatModifier(
                    modifier_type=self.modifier_type,
                    value=self.amount,
                    source=self,
                )
            )

        def remove(self, target: GameObject) -> None:
            get_stat(target, self.stat_id).remove_modifiers_from_source(self)

        @classmethod
        def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
            modifier_name: str = params.get("modifier_type", "FLAT")
            amount: float = float(params["amount"])
            stat_id: str = str(params["stat"])

            modifier_type = StatModifierType[modifier_name.upper()]

            return cls(stat_id=stat_id, amount=amount, modifier_type=modifier_type)


    # Register the effect type with the library
    self._world.resource_manager.get_resource(EffectLibrary).add_effect_type(
        StatBuff
    )


Built-in preconditions
----------------------

- ``HasTrait``: Checks if a GameObject has a trait

  - Parameters:

    - ``trait``: (str) The ID of the trait to check for

- ``TargetHasTrait``: (For social rules only) Checks if the target of the relationship has a trait

  - Parameters:

    - ``trait``: (str) The ID of the trait to check for

- ``SkillRequirement``: Check if the character has a skill level of at least a given level

  - Parameters:

    - ``skill``: (str) The ID of the skill to check
    - ``level``: (int) The required skill level

- ``AtLeastLifeStage``: Check if a character is of at least the given life stage

  - Parameters:

    - ``life_stage``: (str) "CHILD", "ADOLESCENT", "YOUNG_ADULT", "ADULT", or "SENIOR"

- ``TargetIsSex``: (For social rules only) Check if the target of the relationship is a given sex

  - Parameters:

    - ``sex``: (str) "MALE", "FEMALE", or "NOT_SPECIFIED"

- ``TargetLifeStageLT``: (For social rules only) Check if the target of the relationships life stage is less than the given life stage.

  - Parameters:

    - ``life_stage``: (str) "CHILD", "ADOLESCENT", "YOUNG_ADULT", "ADULT", or "SENIOR"

Defining new Preconditions
--------------------------

Defining new `Precondition` subtypes is similar to the process for creating new Effect types. Users need to create a new Python class that inherits from the ``Precondition`` abstract class. You will need to implement all the abstract methods and finally add the class to the ``PreconditionLibrary``.

The follow is an example using the ``HasTrait`` precondition.

.. code-block:: python

    class HasTrait(Precondition):
        """A precondition that check if a GameObject has a given trait."""

        __slots__ = ("trait_id",)

        trait_id: str
        """The ID of the trait to check for."""

        def __init__(self, trait: str) -> None:
            super().__init__()
            self.trait_id = trait

        @property
        def description(self) -> str:
            return f"has the trait {self.trait_id}"

        def __call__(self, target: GameObject) -> bool:
            return has_trait(target, self.trait_id)

        @classmethod
        def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
            trait = params["trait"]
            return cls(trait)

    # Add the precondition class to the library
    self.world.resource_manager.get_resource(PreconditionLibrary).add_precondition_type(
        HasTrait
    )
