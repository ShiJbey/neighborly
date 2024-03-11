"""Built-in Effect Definitions.

This module contains class definitions for effects that may be applied by traits and
social rules.

"""

from __future__ import annotations

from neighborly.components.skills import Skills
from neighborly.components.stats import Stats
from neighborly.ecs import GameObject
from neighborly.effects.base_types import Effect, EffectContext
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.skills import add_skill, has_skill
from neighborly.helpers.traits import remove_trait, add_trait


class AddTrait(Effect):
    """Add trait to a GameObject."""

    __slots__ = ("target", "trait_id", "duration")

    target: GameObject
    """The GameObject to add the trait to."""
    trait_id: str
    """The ID of the trait to add."""
    duration: int
    """The amount of time to apply the trait."""

    def __init__(self, target: GameObject, trait_id: str, duration: int) -> None:
        self.target = target
        self.trait_id = trait_id
        self.duration = duration

    def apply(self) -> None:
        add_trait(self.target, self.trait_id, self.duration)

    @classmethod
    def instantiate(cls, ctx: EffectContext) -> Effect:
        target_var: str = ctx.args[0]
        trait_id: str = ctx.args[1]
        duration: int = int(ctx.args[2])

        target = ctx.world.gameobjects.get_gameobject(
            int(
                str(ctx.bindings[target_var])
            )  # We cant go straight from an obj to an int
        )

        return cls(
            target=target,
            trait_id=trait_id,
            duration=duration,
        )


class RemoveTrait(Effect):
    """Remove a trait from a GameObject."""

    __slots__ = ("target", "trait_id")

    target: GameObject
    """The GameObject to add the trait to."""
    trait_id: str
    """The ID of the trait to add."""

    def __init__(self, target: GameObject, trait_id: str) -> None:
        self.target = target
        self.trait_id = trait_id

    def apply(self) -> None:
        remove_trait(self.target, self.trait_id)

    @classmethod
    def instantiate(cls, ctx: EffectContext) -> Effect:
        target_var: str = ctx.args[0]
        trait_id: str = ctx.args[1]

        target = ctx.world.gameobjects.get_gameobject(
            int(
                str(ctx.bindings[target_var])
            )  # We cant go straight from an obj to an int
        )

        return cls(
            target=target,
            trait_id=trait_id,
        )


class AddRelationshipTrait(Effect):
    """Add trait to a Relationship."""

    __slots__ = ("target", "trait_id", "duration")

    target: GameObject
    """The GameObject to add the trait to."""
    trait_id: str
    """The ID of the trait to add."""
    duration: int
    """The amount of time to apply the trait."""

    def __init__(self, target: GameObject, trait_id: str, duration: int) -> None:
        self.target = target
        self.trait_id = trait_id
        self.duration = duration

    def apply(self) -> None:
        add_trait(self.target, self.trait_id, self.duration)

    @classmethod
    def instantiate(cls, ctx: EffectContext) -> Effect:
        owner_var: str = ctx.args[0]
        target_var: str = ctx.args[1]
        trait_id: str = ctx.args[2]
        duration: int = int(ctx.args[3])

        target = get_relationship(
            ctx.world.gameobjects.get_gameobject(
                int(
                    str(ctx.bindings[owner_var])
                )  # We cant go straight from an obj to an int
            ),
            ctx.world.gameobjects.get_gameobject(
                int(
                    str(ctx.bindings[target_var])
                )  # We cant go straight from an obj to an int
            ),
        )

        return cls(target=target, trait_id=trait_id, duration=duration)


class RemoveRelationshipTrait(Effect):
    """Remove a trait from a relationship."""

    __slots__ = ("target", "trait_id")

    target: GameObject
    """The GameObject whose skill to modify."""
    trait_id: str
    """The ID of the trait."""

    def __init__(self, target: GameObject, trait_id: str) -> None:
        self.target = target
        self.trait_id = trait_id

    def apply(self) -> None:
        remove_trait(self.target, self.trait_id)

    @classmethod
    def instantiate(cls, ctx: EffectContext) -> Effect:
        owner_var: str = ctx.args[0]
        target_var: str = ctx.args[1]
        trait_id: str = ctx.args[2]

        target = get_relationship(
            ctx.world.gameobjects.get_gameobject(
                int(
                    str(ctx.bindings[owner_var])
                )  # We cant go straight from an obj to an int
            ),
            ctx.world.gameobjects.get_gameobject(
                int(
                    str(ctx.bindings[target_var])
                )  # We cant go straight from an obj to an int
            ),
        )

        return cls(
            target=target,
            trait_id=trait_id,
        )


class AddStatBuff(Effect):
    """Add an amount to a GameObject's stat (not a relationship)."""

    __slots__ = ("target", "stat", "amount")

    target: GameObject
    """The GameObject whose skill to modify."""
    stat: str
    """The name of the skill to modify."""
    amount: float
    """The amount to modify the skill by."""

    def __init__(self, target: GameObject, stat: str, amount: float) -> None:
        self.target = target
        self.stat = stat
        self.amount = amount

    def apply(self) -> None:
        stats = self.target.get_component(Stats)
        stats.get_stat(self.stat).base_value += self.amount

    @classmethod
    def instantiate(cls, ctx: EffectContext) -> Effect:
        target_var: str = ctx.args[0]
        stat: str = ctx.args[1]
        amount: float = float(ctx.args[2])

        target = ctx.world.gameobjects.get_gameobject(
            int(
                str(ctx.bindings[target_var])
            )  # We cant go straight from an obj to an int
        )

        return cls(
            target=target,
            stat=stat,
            amount=amount,
        )


class AddRelationshipStatBuff(Effect):
    """Add an amount a relationship's stat's base value."""

    __slots__ = ("target", "stat", "amount")

    target: GameObject
    """The GameObject whose skill to modify."""
    stat: str
    """The name of the skill to modify."""
    amount: float
    """The amount to modify the skill by."""

    def __init__(self, target: GameObject, stat: str, amount: float) -> None:
        self.target = target
        self.stat = stat
        self.amount = amount

    def apply(self) -> None:
        stats = self.target.get_component(Stats)
        stats.get_stat(self.stat).base_value += self.amount

    @classmethod
    def instantiate(cls, ctx: EffectContext) -> Effect:
        owner_var: str = ctx.args[0]
        target_var: str = ctx.args[1]
        stat: str = ctx.args[2]
        amount: float = float(ctx.args[3])

        target = get_relationship(
            ctx.world.gameobjects.get_gameobject(
                int(
                    str(ctx.bindings[owner_var])
                )  # We cant go straight from an obj to an int
            ),
            ctx.world.gameobjects.get_gameobject(
                int(
                    str(ctx.bindings[target_var])
                )  # We cant go straight from an obj to an int
            ),
        )

        return cls(
            target=target,
            stat=stat,
            amount=amount,
        )


class AddSkillBuff(Effect):
    """Add an amount to a skill's base value."""

    __slots__ = ("target", "skill", "amount")

    target: GameObject
    """The GameObject whose skill to modify."""
    skill: str
    """The name of the skill to modify."""
    amount: float
    """The amount to modify the skill by."""

    def __init__(self, target: GameObject, skill: str, amount: float) -> None:
        self.target = target
        self.skill = skill
        self.amount = amount

    def apply(self) -> None:
        if not has_skill(self.target, self.skill):
            add_skill(self.target, self.skill)

        skills = self.target.get_component(Skills)
        skills.get_skill(self.skill).base_value += self.amount

    @classmethod
    def instantiate(cls, ctx: EffectContext) -> Effect:
        target_var: str = ctx.args[0]
        skill: str = ctx.args[1]
        amount: float = float(ctx.args[2])

        target = ctx.world.gameobjects.get_gameobject(
            int(
                str(ctx.bindings[target_var])
            )  # We cant go straight from an obj to an int
        )

        return cls(
            target=target,
            skill=skill,
            amount=amount,
        )
