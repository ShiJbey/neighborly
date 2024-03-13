"""Neighborly ECS Event.

"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, ClassVar, Generic, TypeVar

import attrs
from ordered_set import OrderedSet


@attrs.define(slots=True, kw_only=True)
class Event:
    """A signal that something has happened in the simulation."""

    __event_id__: ClassVar[str] = ""

    data: dict[str, Any] = attrs.field(factory=dict)
    """The name of this event."""

    @property
    def event_id(self) -> str:
        """The ID of the event."""
        return self.__event_id__ if self.__event_id__ else self.__class__.__name__


_T = TypeVar("_T", bound=Event)


class EventEmitter(Generic[_T]):
    """Emits events that observers can listen for."""

    __slots__ = ("listeners",)

    listeners: list[Callable[[object, _T], None]]

    def __init__(self) -> None:
        super().__init__()
        self.listeners = []

    def add_listener(
        self,
        listener: Callable[[object, _T], None],
    ) -> None:
        """Register a listener function to a specific event type.

        Parameters
        ----------
        listener
            A function to be called when the given event type fires.
        """
        self.listeners.append(listener)

    def remove_listener(
        self,
        listener: Callable[[object, _T], None],
    ) -> None:
        """Remove a listener from an event type.

        Parameters
        ----------
        listener
            A listener callback.
        """
        self.listeners.remove(listener)

    def remove_all_listeners(self) -> None:
        """Remove all listeners from an event.

        Parameters
        ----------
        event_name
            The name of the event.
        """
        self.listeners.clear()

    def dispatch(self, source: object, event: _T) -> None:
        """Fire an event and trigger associated event listeners.

        Parameters
        ----------
        source
            The source of the event
        event
            The event to fire
        """

        for callback_fn in self.listeners:
            callback_fn(source, event)


class EventManager:
    """Manages event listeners for a single World instance."""

    __slots__ = ("_event_listeners_by_type",)

    _event_listeners_by_type: defaultdict[str, OrderedSet[Callable[[Event], None]]]
    """Event listeners that are only called when a specific type of event fires."""

    def __init__(self) -> None:
        self._event_listeners_by_type = defaultdict(OrderedSet)

    def add_listener(
        self,
        event_name: str,
        listener: Callable[[Event], None],
    ) -> None:
        """Register a listener function to a specific event type.

        Parameters
        ----------
        event_name
            The name of the event.
        listener
            A function to be called when the given event type fires.
        """
        self._event_listeners_by_type[event_name].add(listener)

    def remove_listener(
        self,
        event_name: str,
        listener: Callable[[Event], None],
    ) -> None:
        """Remove a listener from an event type.

        Parameters
        ----------
        event_name
            The name of the event.
        listener
            A listener callback.
        """
        self._event_listeners_by_type[event_name].remove(listener)

    def remove_all_listeners(self, event_name: str) -> None:
        """Remove all listeners from an event.

        Parameters
        ----------
        event_name
            The name of the event.
        """
        del self._event_listeners_by_type[event_name]

    def dispatch_event(self, event: Event) -> None:
        """Fire an event and trigger associated event listeners.

        Parameters
        ----------
        event
            The event to fire
        """

        for callback_fn in self._event_listeners_by_type.get(
            event.event_id, OrderedSet([])
        ):
            callback_fn(event)
