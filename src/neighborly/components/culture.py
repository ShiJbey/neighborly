from abc import ABC
from typing import Any, ClassVar, Dict, List, Optional

import attrs

from neighborly.core.ecs import Component, GameObject, ISerializable, TagComponent


@attrs.define
class MarriageConfig:
    """A component that tracks configuration settings for marriage."""

    spouse_prefabs: List[str] = attrs.field(factory=list)
    """The names the prefabs of potential spouses when spawning a character."""

    chance_spawn_with_spouse: float = 0.5
    """The probability of this character spawning with a spouse."""


class CultureType(TagComponent, ABC):
    marriage_config: ClassVar[Optional[MarriageConfig]] = None
    """Configuration settings for this character getting married."""


class Culture(Component, ISerializable):
    """Tracks a reference to a character's culture type component."""

    __slots__ = "_culture_type"

    _culture_type: CultureType
    """A reference to a character's culture type component."""

    def __init__(self, species_type: CultureType) -> None:
        super().__init__()
        self._culture_type = species_type

    def on_add(self, gameobject: GameObject) -> None:
        gameobject.add_component(self._culture_type)

    def on_remove(self, gameobject: GameObject) -> None:
        gameobject.remove_component(type(self._culture_type))

    @property
    def culture_type(self) -> CultureType:
        """A reference to a character's culture type component."""
        return self._culture_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "species_type": type(self.culture_type).__name__
        }

    def __repr__(self) -> str:
        return "{}({})".format(
            type(self).__name__,
            type(self.culture_type).__name__
        )
