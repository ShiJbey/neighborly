"""Event Emitters

This module contains an implementation of the EventEmitter class which is a
Python re-implementation of CSharp Event delegates.

"""

from typing import Callable, List, TypeVar, Generic, Self


_ET = TypeVar("_ET")


class EventEmitter(Generic[_ET]):
    """Implements a Pub/Sub protocol where listeners can subscribe to receive events."""

    _subscribers: List[Callable[[_ET], None]]

    def __init__(self) -> None:
        self._subscribers = []

    def dispatch(self, data: _ET) -> None:
        for subscriber in reversed(self._subscribers):
            subscriber(data)

    def subscribe(self, subscriber: Callable[[_ET], None]) -> None:
        self._subscribers.append(subscriber)

    def unsubscribe(self, subscriber: Callable[[_ET], None]) -> None:
        self._subscribers.remove(subscriber)

    def __iadd__(self, subscriber: Callable[[_ET], None]) -> Self:
        self._subscribers.append(subscriber)
        return self

    def __isub__(self, subscriber: Callable[[_ET], None]) -> Self:
        self._subscribers.remove(subscriber)
        return self
