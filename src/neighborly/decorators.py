"""
Utility decorators that should assist with content authoring
"""

from typing import Any, Optional, Type, TypeVar

from neighborly.ecs import (
    Component,
    Event,
    EventListener,
    IComponentFactory,
    System,
    SystemGroup,
    World,
)
from neighborly.life_event import RandomLifeEvent, RandomLifeEventLibrary
from neighborly.location_preference import (
    ILocationPreferenceRule,
    LocationPreferenceRuleLibrary,
)
from neighborly.relationship import ISocialRule, SocialRuleLibrary

_CT = TypeVar("_CT", bound=Component)
_CF = TypeVar("_CF", bound=IComponentFactory)
_RT = TypeVar("_RT", bound=Any)
_ST = TypeVar("_ST", bound=System)
_LT = TypeVar("_LT", bound=RandomLifeEvent)
_ET_contra = TypeVar("_ET_contra", bound=Event, contravariant=True)


def component(world: World):
    """Register a component type with the  simulation.

    Registers a component class type with the simulation's World instance.
    This allows content authors to use the Component in YAML files and
    EntityPrefabs.

    Parameters
    ----------
    world
        A world instance.
    """

    def decorator(cls: Type[_CT]) -> Type[_CT]:
        world.gameobject_manager.register_component(cls)
        return cls

    return decorator


def component_factory(world: World, component_type: Type[Component]):
    """Register a component type with the  simulation.

    Registers a component class type with the simulation's World instance.
    This allows content authors to use the Component in YAML files and
    EntityPrefabs.

    Parameters
    ----------
    world
        A world instance.
    component_type
        The component type the factory instantiates.
    """

    def decorator(factory_type: Type[_CF]) -> Type[_CF]:
        world.gameobject_manager.get_component_info(
            component_type.__name__
        ).factory = factory_type
        return factory_type

    return decorator


def resource(world: World, **kwargs: Any):
    """Add a class as a shared resource.

    This decorator adds an instance of the decorated class as a shared resource.

    Parameters
    ----------
    world
        A world instance.
    **kwargs
        Keyword arguments to pass to the constructor of the decorated class.
    """

    def decorator(cls: Type[_RT]) -> Type[_RT]:
        world.resource_manager.add_resource(cls(**kwargs))
        return cls

    return decorator


def system(
    world: World,
    priority: int = 0,
    system_group: Optional[Type[SystemGroup]] = None,
    **kwargs: Any,
):
    """Add a class as a simulation system.

    This decorator adds an instance of the decorated class as a shared resource.

    Parameters
    ----------
    world
        A world instance.
    priority
        The priority of this system relative to others in its group.
    system_group
        The group to add the system to. (defaults to root-level group)
    **kwargs
        Keyword arguments to pass to the constructor of the decorated class.
    """

    def decorator(cls: Type[_ST]) -> Type[_ST]:
        world.system_manager.add_system(
            system=cls(**kwargs), priority=priority, system_group=system_group
        )
        return cls

    return decorator


def random_life_event(world: World):
    """Adds a class type to the registry of random life events"""

    def decorator(cls: Type[_LT]) -> Type[_LT]:
        world.resource_manager.get_resource(RandomLifeEventLibrary).add(cls)
        return cls

    return decorator


def social_rule(world: World):
    """Decorator that marks a function as a location preference rule.

    Parameters
    ----------
    world
        A world instance.
    """

    def decorator(rule: Type[ISocialRule]):
        world.resource_manager.get_resource(SocialRuleLibrary).add_rule(rule())
        return rule

    return decorator


def location_preference_rule(world: World, description: str):
    """Decorator that marks a function as a location preference rule.

    Parameters
    ----------
    world
        A world instance.
    description
        Text description of the rule.
    """

    def decorator(rule: ILocationPreferenceRule):
        world.resource_manager.get_resource(LocationPreferenceRuleLibrary).add(
            rule, description
        )

    return decorator


def on_event(world: World, event_type: Type[_ET_contra]):
    """A decorator that registers a function as an event listener for GameObjects.

    Parameters
    ----------
    world
        A world instance.
    event_type
        The type of event that this function will listen for.
    """

    def decorator(listener: EventListener[_ET_contra]) -> EventListener[_ET_contra]:
        world.event_manager.on_event(event_type, listener)
        return listener

    return decorator


def on_any_event(world: World):
    """A decorator that registers a function as an event listener for GameObjects.

    The decorated function will be called in response to all events fired by
    GameObjects.

    Parameters
    ----------
    world
        A world instance.
    """

    def decorator(listener: EventListener[Event]) -> EventListener[Event]:
        world.event_manager.on_any_event(listener)
        return listener

    return decorator
