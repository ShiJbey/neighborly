"""Neighborly Species Components.

Characters may belong to only one species at a time. Species are used to influence social rules and character behavior.
A character's species affects things like their aging, reproduction, lifespan, and reproduction.

"""
from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar, Dict, List, Optional, Type

import attrs

from neighborly.core.ecs import Component, GameObject, ISerializable, TagComponent


@attrs.define
class AgingConfig:
    """A component that tracks configuration settings for aging."""

    adolescent_age: int
    """The age this species is considered an adolescent."""

    young_adult_age: int
    """The age this species is considered a young-adult."""

    adult_age: int
    """The age this species is considered an adult."""

    senior_age: int
    """The age this species is considered to be a senior."""

    lifespan: int
    """Average number of years this species lives."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adolescent_age": self.adolescent_age,
            "young_adult_age": self.young_adult_age,
            "adult_age": self.adult_age,
            "senior_age": self.senior_age,
        }


@attrs.define
class ReproductionConfig:
    """A component that track configuration settings about reproduction."""

    max_children_at_spawn: int = 3
    """The maximum number of children this character can spawn with."""

    child_prefabs: List[str] = attrs.field(factory=list)
    """The names of prefabs that can spawn as children."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_children_at_spawn": self.max_children_at_spawn
        }


class SpeciesType(TagComponent, ABC):
    aging_config: ClassVar[Optional[AgingConfig]] = None
    reproduction_config: ClassVar[Optional[ReproductionConfig]] = None


class Species(Component, ISerializable):
    """Tracks a reference to a character's species type component."""

    __slots__ = "_species_type"

    _species_type: SpeciesType
    """A reference to a character's species type component."""

    def __init__(self, species_type: SpeciesType) -> None:
        super().__init__()
        self._species_type = species_type

    def on_add(self, gameobject: GameObject) -> None:
        gameobject.add_component(self._species_type)

    def on_remove(self, gameobject: GameObject) -> None:
        gameobject.remove_component(type(self._species_type))

    @property
    def species_type(self) -> SpeciesType:
        """A reference to a character's species type component."""
        return self._species_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "species_type": type(self.species_type).__name__
        }
    
    def __repr__(self) -> str:
        return "{}({})".format(
            type(self).__name__,
            type(self.species_type).__name__
        )


def set_species(character: GameObject, species_type: Type[SpeciesType]) -> None:
    """Sets a character's species. Overwriting any existing species."""

    if character.has_component(Species):
        character.remove_component(Species)
    character.add_component(
        character.world.gameobject_manager.create_component(Species, species_type=species_type)
    )
