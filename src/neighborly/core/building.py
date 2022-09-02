from typing import Any, Dict

from neighborly.core.ecs import Component


class Building(Component):
    """
    Building components are attached to structures (like businesses and residences)
    that are currently present in the town.

    Attributes
    ----------
    building_type: str
        What kind of building is this
    """

    __slots__ = "_building_type"

    def __init__(self, building_type: str) -> None:
        super().__init__()
        self._building_type: str = building_type

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "building_type": self.building_type}

    @property
    def building_type(self) -> str:
        return self._building_type
