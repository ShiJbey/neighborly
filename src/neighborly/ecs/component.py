"""Neighborly ECS Component Implementation.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from neighborly.ecs.game_object import GameObject


class Component(ABC):
    """A collection of data attributes associated with a GameObject."""

    __slots__ = ("_gameobject", "_has_gameobject")

    _gameobject: GameObject
    """The GameObject the component belongs to."""
    # We need an additional variable to track if the gameobject has been set because
    # the variable will be initialized outside the __init__ method, and we need to
    # ensure that it is not set again
    _has_gameobject: bool
    """Is the Component's _gameobject field set."""

    def __init__(self) -> None:
        super().__init__()
        self._has_gameobject = False

    @property
    def gameobject(self) -> GameObject:
        """Get the GameObject instance for this component."""
        return self._gameobject

    @gameobject.setter
    def gameobject(self, value: GameObject) -> None:
        """Sets the component's gameobject reference.

        Notes
        -----
        This setter should only be called internally by the ECS when adding new
        components to gameobjects. Calling this function twice will result in a
        RuntimeError.
        """
        if self._has_gameobject is True:
            raise RuntimeError("Cannot reassign a component to another GameObject.")
        self._gameobject = value

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize the component to a JSON-serializable dictionary."""
        return {}


class TagComponent(Component):
    """Tags a GameObject as active within the simulation."""

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def to_dict(self) -> dict[str, Any]:
        return {}


class Active(TagComponent):
    """Tags a GameObject as active within the simulation."""
