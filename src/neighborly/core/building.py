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
    lot: int
        ID of the lot this building is on
    """

    __slots__ = "building_type", "lot"

    def __init__(self, building_type: str, lot: int) -> None:
        super().__init__()
        self.building_type: str = building_type
        self.lot: int = lot

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "building_type": self.building_type}
