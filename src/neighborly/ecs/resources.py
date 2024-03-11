"""ECS Resource Manager.

"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Type, TypeVar

from neighborly.ecs.errors import ResourceNotFoundError

_RT = TypeVar("_RT", bound="Any")


class ResourceManager:
    """Manages shared resources for a world instance."""

    __slots__ = ("_resources",)

    _resources: dict[Type[Any], Any]
    """Resources shared by the world instance."""

    def __init__(self) -> None:
        self._resources = {}

    @property
    def resources(self) -> Iterable[Any]:
        """Get an iterable of all the current resources."""
        return self._resources.values()

    def add_resource(self, resource: Any) -> None:
        """Add a shared resource to a world.

        Parameters
        ----------
        resource
            The resource to add
        """
        resource_type = type(resource)
        self._resources[resource_type] = resource

    def remove_resource(self, resource_type: Type[Any]) -> None:
        """Remove a shared resource to a world.

        Parameters
        ----------
        resource_type
            The class of the resource.
        """
        try:
            del self._resources[resource_type]
        except KeyError as exc:
            raise ResourceNotFoundError(resource_type.__name__) from exc

    def get_resource(self, resource_type: Type[_RT]) -> _RT:
        """Access a shared resource.

        Parameters
        ----------
        resource_type
            The class of the resource.

        Returns
        -------
        _RT
            The instance of the resource.
        """
        try:
            return self._resources[resource_type]
        except KeyError as exc:
            raise ResourceNotFoundError(resource_type.__name__) from exc

    def has_resource(self, resource_type: Type[Any]) -> bool:
        """Check if a world has a shared resource.

        Parameters
        ----------
        resource_type
            The class of the resource.

        Returns
        -------
        bool
            True if the resource exists, False otherwise.
        """
        return resource_type in self._resources

    def try_resource(self, resource_type: Type[_RT]) -> Optional[_RT]:
        """Attempt to access a shared resource.

        Parameters
        ----------
        resource_type
            The class of the resource.

        Returns
        -------
        _RT or None
            The instance of the resource.
        """
        return self._resources.get(resource_type)
