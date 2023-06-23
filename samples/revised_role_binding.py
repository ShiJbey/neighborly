from __future__ import annotations

from typing import Generator, Optional, Tuple

from neighborly import World
from neighborly.core.ecs import Component, GameObject
from neighborly.core.life_event import (
    EventRoleBindingContext,
    EventRoleConsiderationList,
    RandomLifeEvent,
    event_role,
)
from neighborly.simulation import Neighborly


# @dataclass()
# class RoleCastingContext:
#     """Manages information related to the current state of cast roles."""
#
#     world: World
#     """The world instance that the GameObjects in the role list belong to."""
#
#     bindings: Optional[EventRoleList] = None = field(default_factory=EventRoleList)
#     """The current set of casted roles."""
#
#
# RoleCastingFn = Callable[
#     [RoleCastingContext], Generator[tuple[GameObject, ...], None, None]
# ]
# """Role casting functions yield GameObjects to bind to a role."""
#
# _T = TypeVar("_T", bound="RandomEvent")
#
#
# class EventRoleConsideration(Protocol):
#
#     def __call__(self, gameobject: GameObject, event: _T) -> Optional[float]:
#         raise NotImplementedError()
#
#
# class EventRoleConsiderationList(List[EventRoleConsideration], Generic[_T]):
#     """A collection of considerations associated with an action or goal."""
#
#     def calculate_score(self, gameobject: GameObject, event: _T) -> float:
#         """Scores each consideration for a GameObject and returns the aggregate score.
#
#         Parameters
#         ----------
#         gameobject
#             A GameObject.
#         event
#             The event to consider.
#
#         Returns
#         -------
#         float
#             The aggregate consideration score.
#         """
#
#         cumulative_score: float = 1.0
#         consideration_count: int = 0
#
#         for c in self:
#             consideration_score = c(gameobject, event)
#             if consideration_score is not None:
#                 assert 0.0 <= consideration_score <= 1.0
#                 cumulative_score *= consideration_score
#                 consideration_count += 1
#
#             if cumulative_score == 0.0:
#                 break
#
#         if consideration_count == 0:
#             consideration_count = 1
#             cumulative_score = 0.0
#
#         # Scores are averaged using the Geometric Mean instead of
#         # arithmetic mean. It calculates the mean of a product of
#         # n-numbers by finding the n-th root of the product
#         # Tried using the averaging scheme by Dave Mark, but it
#         # returned values that felt too small and were not easy
#         # to reason about.
#         # Using this method, a cumulative score of zero will still
#         # result in a final score of zero.
#
#         final_score = cumulative_score ** (1 / consideration_count)
#
#         return final_score
#
#
# class EventRoleInfo(object, staticmethod):
#     """A class attribute wrapper that defines a role within a Random Event."""
#
#     __slots__ = "name", "binding_fn", "considerations"
#
#     name: str
#     """The name of the role."""
#
#     binding_fn: RoleCastingFn
#     """The function used to bind GameObject instances to the role."""
#
#     considerations: EventRoleConsiderationList[Any]
#     """A list of considerations for GameObjects bound to this role."""
#
#     def __init__(
#         self,
#         name: str,
#         binding_fn: RoleCastingFn,
#         considerations: EventRoleConsiderationList[Any],
#     ) -> None:
#         super().__init__(binding_fn)
#         self.name = name
#         self.binding_fn = binding_fn
#         self.considerations = considerations
#
#     def __repr__(self) -> str:
#         return f"{type(self).__name__}({self.name})"
#
#
# def event_role(
#     name: str = "", considerations: Optional[EventRoleConsiderationList] = None
# ):
#     """A decorator to indicate that a function is for casting a role"""
#
#     def event_role_decorator(fn):
#
#         @functools.wraps(fn)
#         def wrapper():
#             return EventRoleInfo(
#                 name if name else fn.__name__,
#                 cast(Callable[[RoleCastingContext], Generator[tuple[GameObject, ...], None, None]], fn),
#                 EventRoleConsiderationList(considerations if considerations else []),
#             )
#
#         return wrapper
#
#     return event_role_decorator
#
#
# class RandomEventMeta(type):
#     def __new__(
#         mcls,
#         name: str,
#         bases: tuple[type, ...],
#         namespace: dict[str, Any],
#         /,
#         **kwargs: Any,
#     ):
#         cls = super().__new__(mcls, name, bases, namespace, **kwargs)
#         _update_roles(cls)
#         return cls
#
#
# def _update_roles(cls: type) -> None:
#     """
#     Updates the internal records of event roles for classes that derive from the
#     RandomEventMeta metaclass.
#
#     Parameters
#     ----------
#     cls
#         The class type to process
#
#     Notes
#     -----
#     This function is modeled after the update_abstractmethods function in abc.py
#     """
#     event_roles: list[EventRoleInfo] = []
#
#     # Check the existing event role methods of the parents
#     for base_class in cls.__bases__:
#         for entry in getattr(base_class, "__event_roles__", ()):
#             if isinstance(entry, EventRoleInfo):
#                 event_roles.append(entry)
#
#     # Check the declared event role methods
#     for _, value in cls.__dict__.items():
#         if isinstance(value, EventRoleInfo):
#             event_roles.append(value)
#
#     # Set combined collection of event roles for the given type
#     setattr(cls, "__event_roles__", tuple(event_roles))
#
#
# @dataclass
# class RoleSearchState:
#     """A saved state for backtracking when searching for roles to bind."""
#
#     ctx: RoleCastingContext
#     """The current context to pass to the binding function."""
#
#     role_to_cast: EventRoleInfo
#     """The current role being bound during this state."""
#
#     binding_generator: Generator[tuple[GameObject, ...], None, None]
#     """The generator function providing the next set of results."""
#
#     pending: list[EventRoleInfo]
#     """A queue of remaining event roles to bind."""
#
#
# class RandomEvent(metaclass=RandomEventMeta):
#     """Helper class that provides a standard way to create a random event using
#     inheritance.
#     """
#
#     __slots__ = "timestamp", "roles"
#
#     __event_roles__: ClassVar[list[EventRoleInfo]] = []
#     """All role binding functions"""
#
#     timestamp: SimDateTime
#     """When did this event occur."""
#
#     roles: EventRoleList
#     """Who/What is involved."""
#
#     def __init__(self, timestamp: SimDateTime, roles: EventRoleList) -> None:
#         self.timestamp = timestamp
#         self.roles = roles
#
#     def __repr__(self) -> str:
#         return "{}(timestamp:{}, roles:{})".format(
#             type(self).__name__, str(self.timestamp), str(self.roles)
#         )
#
#     def get_probability(self) -> float:
#         probability = 1.0
#         contributor_count = 0
#
#         for role in self.__event_roles__:
#             if role.considerations:
#                 for gameobject in self.roles.get_all(role.name):
#                     probability *= role.considerations.calculate_score(gameobject, self)
#                     contributor_count += 1
#
#         if contributor_count > 0:
#             # Take the arithmetic mean of the contributing probability scores
#             return probability ** (1 / contributor_count)
#         else:
#             return 0.5
#
#     @classmethod
#     def instantiate(
#         cls, world: World, bindings: Optional[EventRoleList] = None
#     ) -> Generator[RandomEvent, None, None]:
#         # Check if there are any roles that need to be bound
#         if len(cls.__event_roles__) == 0:
#             yield cls(world.get_resource(SimDateTime).copy(), EventRoleList())
#             return
#
#         # Stack of previous search states for when we fail to find a result
#         history: list[RoleSearchState] = []
#
#         # Starting context uses the given bindings
#         ctx = RoleCastingContext(
#             world=world, bindings=bindings if bindings else EventRoleList()
#         )
#
#         # Set up the initial state for binding
#         current_state = RoleSearchState(
#             ctx=ctx,
#             role_to_cast=cls.__event_roles__[0],
#             binding_generator=cls.__event_roles__[0].binding_fn(ctx),
#             pending=cls.__event_roles__[1:],
#         )
#
#         while True:
#             try:
#                 if len(current_state.pending) > 0:
#                     # Find a single solution add this state to the stack and change the
#                     # current state
#
#                     new_bindings = EventRoleList(
#                         [
#                             *current_state.ctx.bindings,
#                             *[
#                                 EventRole(current_state.role_to_cast.name, r)
#                                 for r in next(current_state.binding_generator)
#                             ],
#                         ]
#                     )
#
#                     # Add the current state to the history and keep iterating
#                     history.append(current_state)
#
#                     # Create a new context and state with the new bindings
#                     new_ctx = RoleCastingContext(
#                         world=world,
#                         bindings=new_bindings,
#                     )
#
#                     current_state = RoleSearchState(
#                         ctx=new_ctx,
#                         role_to_cast=current_state.pending[0],
#                         binding_generator=current_state.pending[0].binding_fn(new_ctx),
#                         pending=current_state.pending[1:],
#                     )
#                 else:
#                     # This is the last role we need to bind.
#                     # Exhaust all the solutions and return them as instances of the
#                     # event
#                     for results in current_state.binding_generator:
#                         # Create combined list of bindings
#                         new_bindings = EventRoleList(
#                             [
#                                 *current_state.ctx.bindings,
#                                 *[
#                                     EventRole(current_state.role_to_cast.name, r)
#                                     for r in results
#                                 ],
#                             ]
#                         )
#
#                         # yield an instance of the random event
#                         yield cls(world.get_resource(SimDateTime).copy(), new_bindings)
#
#                     # Check if there is any history to backtrack through.
#                     # Return if not
#                     if history:
#                         current_state = history.pop()
#                     else:
#                         return
#
#             except StopIteration:
#                 # We failed to find any more results. Pop the history stack and try
#                 # again. Or stop if we have not history
#                 if history:
#                     current_state = history.pop()
#                 else:
#                     return


def sample_consideration(
    gameobject: GameObject, event: StartHeroStory
) -> Optional[float]:
    return 0.1


# noinspection PyNestedDecorators
class StartHeroStory(RandomLifeEvent):
    """Begins a story of a hero versus a villain."""

    def execute(self, world: World) -> None:
        pass

    @event_role(considerations=EventRoleConsiderationList([lambda gameobject, event: 0.8]))
    @staticmethod
    def hero(
        ctx: EventRoleBindingContext,
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        """Bind a hero."""
        for guid, _ in ctx.world.get_component(Hero):
            yield (ctx.world.get_gameobject(guid),)

    @event_role(considerations=EventRoleConsiderationList([sample_consideration]))
    @staticmethod
    def villain(
        ctx: EventRoleBindingContext,
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        """Bind a villain."""
        for guid, _ in ctx.world.get_component(Villain):
            yield (ctx.world.get_gameobject(guid),)


class Hero(Component):
    pass


class Villain(Component):
    pass


def main() -> None:
    sim = Neighborly()

    sim.world.spawn_gameobject([Hero()], name="Miles")
    sim.world.spawn_gameobject([Hero()], name="Peter")
    sim.world.spawn_gameobject([Hero()], name="Gwen")

    sim.world.spawn_gameobject([Villain()], name="KingPin")
    sim.world.spawn_gameobject([Villain()], name="Green Goblin")
    sim.world.spawn_gameobject([Villain()], name="The Prowler")
    sim.world.spawn_gameobject([Villain()], name="Doc. Oc")

    for result in StartHeroStory.instantiate(sim.world):
        print(result.__repr__())
        print(f"Probability: {result.get_probability()}")
        print("===")


if __name__ == "__main__":
    main()
