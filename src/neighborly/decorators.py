"""
Utility decorators that should assist with content authoring
"""

from typing import Any, Type, TypeVar

from neighborly.core.ecs import (
    Component,
    Event,
    GameObject,
    IComponentFactory,
    ISystem,
    EventListener,
)
from neighborly.core.life_event import RandomLifeEvent, RandomLifeEvents
from neighborly.core.location_bias import ILocationBiasRule, LocationBiasRules
from neighborly.core.relationship import ISocialRule, SocialRules
from neighborly.simulation import Neighborly

_CT = TypeVar("_CT", bound=Component)
_CF = TypeVar("_CF", bound=IComponentFactory)
_RT = TypeVar("_RT", bound=Any)
_ST = TypeVar("_ST", bound=ISystem)
_LT = TypeVar("_LT", bound=RandomLifeEvent)
_ET_contra = TypeVar("_ET_contra", bound=Event, contravariant=True)


def component(sim: Neighborly):
    """Register a component type with the  simulation.

    Registers a component class type with the simulation's World instance.
    This allows content authors to use the Component in YAML files and
    EntityPrefabs.

    Parameters
    ----------
    sim
        The simulation instance to register the life event to.
    """

    def decorator(cls: Type[_CT]) -> Type[_CT]:
        sim.world.register_component(cls)
        return cls

    return decorator


def component_factory(sim: Neighborly, component_type: Type[Component], **kwargs: Any):
    """Register a component type with the  simulation.

    Registers a component class type with the simulation's World instance.
    This allows content authors to use the Component in YAML files and
    EntityPrefabs.

    Parameters
    ----------
    sim
        The simulation instance to register the life event to.
    component_type
        The component type the factory instantiates.
    """

    def decorator(cls: Type[_CF]) -> Type[_CF]:
        sim.world.get_component_info(component_type.__name__).factory = cls(**kwargs)
        return cls

    return decorator


def resource(sim: Neighborly, **kwargs: Any):
    """Add a class as a shared resource.

    This decorator adds an instance of the decorated class as a shared resource.

    Parameters
    ----------
    sim
        The simulation instance to register the life event to.
    **kwargs
        Keyword arguments to pass to the constructor of the decorated class.
    """

    def decorator(cls: Type[_RT]) -> Type[_RT]:
        sim.world.add_resource(cls(**kwargs))
        return cls

    return decorator


def system(sim: Neighborly, **kwargs: Any):
    """Add a class as a simulation system.

    This decorator adds an instance of the decorated class as a shared resource.

    Parameters
    ----------
    sim
        The simulation instance to register the life event to.
    **kwargs
        Keyword arguments to pass to the constructor of the decorated class.
    """

    def decorator(cls: Type[_ST]) -> Type[_ST]:
        sim.world.add_system(cls(**kwargs))
        return cls

    return decorator


def random_life_event():
    """Adds a class type to the registry of random life events"""

    def decorator(cls: Type[_LT]) -> Type[_LT]:
        RandomLifeEvents.add(cls)
        return cls

    return decorator


def social_rule(description: str):
    """Decorator that marks a function as a location bias rule.

    Parameters
    ----------
    description
        Text description of the rule.
    """

    def decorator(rule: ISocialRule):
        SocialRules.add(rule, description)
        return rule

    return decorator


def location_bias_rule(description: str):
    """Decorator that marks a function as a location bias rule.

    Parameters
    ----------
    description
        Text description of the rule.
    """

    def decorator(rule: ILocationBiasRule):
        LocationBiasRules.add(rule, description)

    return decorator


def on_event(event_type: Type[_ET_contra]):
    """A decorator that registers a function as an event listener for GameObjects.

    Parameters
    ----------
    event_type
        The type of event that this function will listen for.
    """

    def decorator(listener: EventListener[_ET_contra]) -> EventListener[_ET_contra]:
        GameObject.on(event_type, listener)
        return listener

    return decorator


def on_any_event(listener: EventListener[Event]):
    """A decorator that registers a function as an event listener for GameObjects.

    The decorated function will be called in response to all events fired by
    GameObjects.
    """
    GameObject.on_any(listener)
    return listener
