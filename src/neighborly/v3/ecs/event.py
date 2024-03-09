"""Neighborly ECS Event.

"""


class Event:
    """A signal that something has happened in the simulation."""

    __slots__ = ("event_name",)

    event_name: str
    """The name of this event."""

    def __init__(self, event_name: str) -> None:
        self.event_name = event_name


class EventManager:
    """Manages event listeners for a single World instance."""

    __slots__ = (
        "_general_event_listeners",
        "_event_listeners_by_type",
        "_world",
        "_next_event_id",
    )

    _world: World
    """The world instance associated with the SystemManager."""
    _next_event_id: int
    """The ID number to be given to the next constructed event."""
    _general_event_listeners: OrderedSet[Callable[[Event], None]]
    """Event listeners that are called when any event fires."""
    _event_listeners_by_type: dict[Type[Event], OrderedSet[Callable[[Event], None]]]
    """Event listeners that are only called when a specific type of event fires."""

    def __init__(self, world: World) -> None:
        self._world = world
        self._general_event_listeners = OrderedSet([])
        self._event_listeners_by_type = {}
        self._next_event_id = 0

    def on_event(
        self,
        event_type: Type[_ET_contra],
        listener: Callable[[_ET_contra], None],
    ) -> None:
        """Register a listener function to a specific event type.

        Parameters
        ----------
        event_type
            The type of event to listen for.
        listener
            A function to be called when the given event type fires.
        """
        if event_type not in self._event_listeners_by_type:
            self._event_listeners_by_type[event_type] = OrderedSet([])
        listener_set = cast(
            OrderedSet[Callable[[_ET_contra], None]],
            self._event_listeners_by_type[event_type],
        )
        listener_set.add(listener)

    def on_any_event(self, listener: Callable[[Event], None]) -> None:
        """Register a listener function to all event types.

        Parameters
        ----------
        listener
            A function to be called any time an event fires.
        """
        self._general_event_listeners.append(listener)

    def dispatch_event(self, event: Event) -> None:
        """Fire an event and trigger associated event listeners.

        Parameters
        ----------
        event
            The event to fire
        """

        for callback_fn in self._event_listeners_by_type.get(
            type(event), OrderedSet([])
        ):
            callback_fn(event)

        for callback_fn in self._general_event_listeners:
            callback_fn(event)

    def get_next_event_id(self) -> int:
        """Get an ID number for a new event instance."""
        event_id = self._next_event_id
        self._next_event_id += 1
        return event_id
