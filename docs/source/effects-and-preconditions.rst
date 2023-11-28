.. _effects_preconditions:

Effects and Preconditions
=========================

When building our simulations, there may be times when we want traits or job roles to have side-effects on characters. For example, maybe we want:

- Customer service jobs to gradually increase a character's sociability stat
- A ``flirtatious`` trait that makes other characters more likely attracted to the flirtatious character.
- Require characters to have a high enough ``cooking`` skill before they become the owner of a restaurant.
- Make characters with the ``shopaholic`` trait to frequent shopping locations.

All these scenarios are accomplished through using :py:class:`~neighborly.effects.base_types.Effect` and :py:class:`~neighborly.preconditions.base_types.Precondition` types.

:py:class:`~neighborly.effects.base_types.Effect` objects perform modifications to a GameObject when applied and undo their modifications when removed. Effects are used with traits and social rules to make changes to characters and relationships.

:py:class:`~neighborly.preconditions.base_types.Precondition` objects check GameObjects for certain conditions. If these conditions are met, they return true.

Using effects and preconditions
-------------------------------

Effects are specified within the ``effects`` section of traits. Each effect ``type`` is internally mapped to a class type of the same name that inherits from Neighborly's ``Effect`` base class. Within the key-value pair specification, all other key-value pairs aside from the ``type`` key are passed to a function that constructs a new instance of that effect type.

The example below shows a trait with multiple effects. All effects are applied when a trait is attached. One of the effects adds a new location preference rule that accepts a list of preconditions. Like effects, precondition specifications require the user to provide a `type: ...`, and all other key-value pairs are used to parameterize an instance of that precondition type. Here we specify that this location preference only applies to places that serve alcohol.

Below is an example of a ``drinks_too_much`` trait definition as it would appear in a JSON data file.

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

Below is the same trait defined using YAML.

.. code-block:: yaml

    drinks_too_much:
        display_name: Drinks too much
        effects:
            - type: StatBuff
              stat: health_decay
              amount: 0.05
              modifier_type: FLAT # <-- This is optional (defaults to FLAT)
            - type: AddLocationPreference
              preconditions:
                - type: HasTrait
                  trait: serves_alcohol
              amount: 0.2


Finally, this is how this trait might be defined directly within Python.

.. code-block:: python

    trait_lib = sim.world.resource_manager.get_resource(TraitLibrary)

    trait_lib.add_definition_from_obj(
        {
            "definition_id": "drinks_too_much",
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
    )

Built-in effects
----------------

Below are a list of all the currently built-in effect types. If users want to add more, they can create a new subclass of ``Effect`` and register their effect type using.

.. code-block:: python

    sim.world.resource_manager.get_resource(EffectLibrary).add_effect_type(CustomEffect)


- :py:class:`neighborly.effects.effects.StatBuff`
- :py:class:`neighborly.effects.effects.IncreaseSkill`
- :py:class:`neighborly.effects.effects.AddSocialRule`
- :py:class:`neighborly.effects.effects.AddLocationPreference`

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
