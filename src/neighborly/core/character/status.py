

from abc import abstractmethod
from typing import Any, Dict, List, Protocol


class Status(Protocol):
    """A temporary or permanent status applied to a GameCharacter"""

    @abstractmethod
    def get_name(self) -> str:
        """Return the name associated with this status"""
        raise NotImplementedError()

    @abstractmethod
    def update(self, **kwargs) -> bool:
        """Update status and return True is still active"""
        raise NotImplementedError()


class StatusManager:
    """Keeps track of statuses that are active on a character"""

    __slots__ = "_statuses"

    def __init__(self) -> None:
        self._statuses: Dict[str, Status] = {}

    def add_status(self, status: Status) -> None:
        """Add a status (may overwrite previous status of same type)"""
        self._statuses[status.get_name()] = status

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


class AdultStatus:
    """Marks a character as being seen as an adult in society"""

    def get_name(self) -> str:
        """Return the name associated with this status"""
        return "adult"

    def update(self, **kwargs) -> bool:
        """Update status and return True is still active"""
        del kwargs
        return True


class ChildStatus:
    """Marks a character as being seen as an child in society"""

    def get_name(self) -> str:
        """Return the name associated with this status"""
        return "child"

    def update(self, **kwargs) -> bool:
        """Update status and return True is still active"""
        del kwargs
        return True


class SeniorStatus:
    """Marks a character as being seen as a senior in society"""

    def get_name(self) -> str:
        """Return the name associated with this status"""
        return "senior"

    def update(self, **kwargs) -> bool:
        """Update status and return True is still active"""
        del kwargs
        return True


class AliveStatus:
    """Marks a character as being alive"""

    def get_name(self) -> str:
        """Return the name associated with this status"""
        return "alive"

    def update(self, **kwargs) -> bool:
        """Update status and return True is still active"""
        del kwargs
        return True


class DeadStatus:
    """Marks a character as being dead"""

    def get_name(self) -> str:
        """Return the name associated with this status"""
        return "dead"

    def update(self, **kwargs) -> bool:
        """Update status and return True is still active"""
        del kwargs
        return True


class DatingStatus:
    """Signals that this character is dating someone"""

    __slots__ = "significant_other"

    def __init__(self, significant_other: int) -> None:
        self.significant_other: int = significant_other

    def get_name(self) -> str:
        """Return the name associated with this status"""
        return "dating"

    def update(self, **kwargs) -> bool:
        """Update status and return True is still active"""
        del kwargs
        return True
