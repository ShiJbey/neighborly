from abc import abstractmethod, ABC
from typing import Any, Dict, List

from neighborly.core.character.character import GameCharacter
from neighborly.core.ecs import World, Component


class Status(ABC):
    """A temporary or permanent status applied to a GameCharacter"""

    tag: str

    def __init__(self, metadata: Dict[str, Any], behaviors: List[str]) -> None:
        self.metadata = {**metadata}
        self.behaviors = [*behaviors]

    @classmethod
    def get_tag(cls) -> str:
        """Return the tag associated with this class"""
        return cls.tag

    @classmethod
    def check_preconditions(cls, world: World, character: GameCharacter) -> bool:
        """Return true if the given character passes the preconditions"""
        raise NotImplementedError()

    @abstractmethod
    def update(self, world: World, character: GameCharacter) -> bool:
        """Update status and return True is still active"""
        raise NotImplementedError()


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
            is_active = status.update(**kwargs)
            if not is_active:
                inactive.append(name)

        for name in inactive:
            self.remove_status(name)
