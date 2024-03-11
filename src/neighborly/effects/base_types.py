"""Abstract base types for implementing Effects.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from neighborly.ecs import World


class EffectContext:
    """Manages information used to create Effects."""

    __slots__ = ("world", "description_template", "bindings", "args")

    world: World
    """The world instance."""
    description_template: str
    """A template string for creating the final description."""
    bindings: dict[str, object]
    """Bindings to pass to RePraxis queries."""
    args: tuple[str, ...]
    """Arguments to pass to the effect factory."""

    def __init__(
        self,
        world: World,
        description_template: str,
        bindings: dict[str, object],
        args: tuple[str, ...],
    ) -> None:
        self.world = world
        self.description_template = description_template
        self.bindings = bindings
        self.args = args

    @property
    def description(self) -> str:
        """The description of this context with all variables filled."""
        final_description = self.description_template

        for variable_name, value in self.bindings:
            final_description = final_description.replace(
                f"[{variable_name[1:]}]", str(value)
            )

        return final_description

    def with_bindings(self, bindings: dict[str, object]) -> EffectContext:
        """Create a new context, updating the existing bindings with the given ones."""

        return EffectContext(
            self.world,
            self.description_template,
            {**self.bindings, **bindings},
            self.args,
        )


class Effect(ABC):
    """Abstract base class for all effect objects."""

    __effect_name__: ClassVar[str] = ""

    @abstractmethod
    def apply(self) -> None:
        """Apply the effects of this effect."""
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def instantiate(cls, ctx: EffectContext) -> Effect:
        """Construct a new instance of the effect type using a data dict."""
        raise NotImplementedError()
