from abc import ABC
from typing import Any, Dict, List

from neighborly.core.ecs import Component, GameObject
from neighborly.core.engine import AbstractFactory, ComponentSpec


class Status(ABC):
    """A temporary or permanent status applied to a GameObject"""

    __slots__ = "_name", "_description", "_metadata"

    def __init__(self, name: str, description: str, metadata: Dict[str, Any]) -> None:
        self._name: str = name
        self._description: str = description
        self._metadata = {**metadata}

    def get_tag(self) -> str:
        """Return the tag associated with this class"""
        return self._name

    def get_description(self) -> str:
        """Return the description for this status"""
        return self._description

    def update(self, gameobject: GameObject, **kwargs) -> bool:
        """Update status and return True is still active"""
        return True

    def __getitem__(self, item: str) -> Any:
        """Get an item from the metadata"""
        return self._metadata[item]


class StatusManager(Component):
    """Keeps track of statuses that are active on a character"""

    __slots__ = "_statuses"

    def __init__(self) -> None:
        super().__init__()
        self._statuses: Dict[str, Status] = {}

    def add_status(self, status: Status) -> None:
        """Add a status (may overwrite previous status of same type)"""
        self._statuses[status.get_tag()] = status

    def has_status(self, status: str) -> bool:
        """Return True if this status is present"""
        return status in self._statuses

    def get_status(self, status: str) -> Any:
        """Return the status with the given name"""
        return self._statuses[status]

    def remove_status(self, status: str) -> None:
        """Remove status with the given name"""
        del self._statuses[status]

    def update(self, **kwargs) -> None:
        """Update all the active statuses and remove inactive ones"""
        inactive: List[str] = []

        for name, status in self._statuses.items():
            is_active = status.update(self.gameobject, **kwargs)
            if not is_active:
                inactive.append(name)

        for name in inactive:
            self.remove_status(name)


class StatusManagerFactory(AbstractFactory):

    def __init__(self):
        super().__init__("StatusManager")

    def create(self, spec: ComponentSpec) -> StatusManager:
        return StatusManager()
