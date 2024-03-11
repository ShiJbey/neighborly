"""Neighborly ECS Event.

"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

import attrs
from ordered_set import OrderedSet


@attrs.define(slots=True)
class Event:
    """A signal that something has happened in the simulation."""

    data: dict[str, Any] = attrs.field(factory=dict)
    """The name of this event."""


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
            event.__class__.__name__, OrderedSet([])
        ):
            callback_fn(event)
