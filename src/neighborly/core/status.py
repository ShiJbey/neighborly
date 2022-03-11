from typing import Any, Dict, List, Callable, Optional

from neighborly.core.ecs import Component, GameObject
from neighborly.core.engine import AbstractFactory, ComponentSpec

StatusUpdateFn = Callable[[GameObject, Dict[str, Any], ...], bool]


class StatusTypeNotFoundError(Exception):
    """Error raised when a status type is not found"""

    def __init__(self, status_type: str) -> None:
        super().__init__(f"No status type found for name, '{status_type}'")
        self.message = f"No status type found for name, '{status_type}'"

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return self.message


class StatusType:
    """Static data about a specific type of status"""

    __slots__ = "_name", "_description", "_update_fn"

    _type_registry: Dict[str, 'StatusType'] = {}

    def __init__(
            self,
            name: str,
            description: str,
            update_fn: Optional[StatusUpdateFn] = None
    ) -> None:
        self._name: str = name
        self._description: str = description
        if update_fn:
            self._update_fn: StatusUpdateFn = update_fn
        else:
            def fn(*args, **kwargs) -> bool:
                return True

            self._update_fn: StatusUpdateFn = fn

    @property
    def name(self) -> str:
        """Return the name of this type"""
        return self._name

    @property
    def description(self) -> str:
        """Return the description for this type"""
        return self._description

    @property
    def update_fn(self) -> StatusUpdateFn:
        """Return the update function for this type"""
        return self._update_fn

    @classmethod
    def register_type(cls, status_type: 'StatusType') -> None:
        """Add a StatusType to the registry"""
        cls._type_registry[status_type.name] = status_type

    @classmethod
    def get_registered_type(cls, status_type: str) -> 'StatusType':
        """Get a status type from the registry"""
        try:
            return cls._type_registry[status_type]
        except KeyError as e:
            raise StatusTypeNotFoundError(status_type) from e


class Status:
    """A temporary or permanent status applied to a GameObject"""

    __slots__ = "_type", "_metadata"

    def __init__(self, status_type: StatusType, metadata: Optional[Dict[str, Any]] = None) -> None:
        self._type: StatusType = status_type
        self._metadata = {**metadata} if metadata else {}

    def get_type(self) -> StatusType:
        """Get the Status' type"""
        return self._type

    def update(self, gameobject: GameObject, **kwargs) -> bool:
        """Update status and return True is still active"""
        return self.get_type().update_fn(gameobject, self._metadata, **kwargs)

    def __getitem__(self, item: str) -> Any:
        """Get an item from the metadata or StatusType Attributes"""
        if item in self._metadata:
            return self._metadata[item]
        return getattr(self._type, item)

    @classmethod
    def create(cls, type_name: str, metadata: Optional[Dict[str, Any]] = None) -> 'Status':
        status_type = StatusType.get_registered_type(type_name)
        return cls(status_type, metadata)


class StatusManager(Component):
    """Keeps track of statuses that are active on a character"""

    __slots__ = "_statuses"

    def __init__(self) -> None:
        super().__init__()
        self._statuses: Dict[str, Status] = {}

    def add_status(self, status: Status) -> None:
        """Add a status (may overwrite previous status of same type)"""
        self._statuses[status.get_type().name] = status

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
