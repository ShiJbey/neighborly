"""
Utility decorators that should assist with content authoring
"""
from typing import Any, Callable, Optional, Type, TypeVar

from neighborly.core.ecs import Component, Event, GameObject, IComponentFactory, ISystem
from neighborly.core.life_event import ActionableLifeEvent, RandomLifeEvents
from neighborly.core.location_bias import ILocationBiasRule, LocationBiasRules
from neighborly.core.relationship import ISocialRule, SocialRules
from neighborly.simulation import Neighborly

_CT = TypeVar("_CT", bound=Component)
_CF = TypeVar("_CF", bound=IComponentFactory)
_RT = TypeVar("_RT", bound=Any)
_ST = TypeVar("_ST", bound=ISystem)
_LT = TypeVar("_LT", bound=ActionableLifeEvent)


def component(sim: Neighborly):
    """Register a component type with the  simulation

    Registers a component class type with the simulation's World instance.
    This allows content authors to use the Component in YAML files and
    EntityPrefabs.

    Parameters
    ----------
    sim: Neighborly
        The simulation instance to register the life event to
    """

    def decorator(cls: Type[_CT]) -> Type[_CT]:
        sim.world.register_component(cls)
        return cls

    return decorator


def component_factory(sim: Neighborly, component_type: Type[Component], **kwargs: Any):
    """Register a component type with the  simulation

    Registers a component class type with the simulation's World instance.
    This allows content authors to use the Component in YAML files and
    EntityPrefabs.

    Parameters
    ----------
    sim: Neighborly
        The simulation instance to register the life event to
    component_type: Type[Component]
        The component type the factory instantiates
    """

    def decorator(cls: Type[_CF]) -> Type[_CF]:
        sim.world.get_component_info(component_type.__name__).factory = cls(**kwargs)
        return cls

    return decorator


def resource(sim: Neighborly, **kwargs: Any):
    """Add a class as a shared resource

    This decorator adds an instance of the decorated class as a shared resource.

    Parameters
    ----------
    sim: Neighborly
        The simulation instance to register the life event to
    **kwargs: Any
        Keyword arguments to pass to the constructor of the decorated class
    """

    def decorator(cls: Type[_RT]) -> Type[_RT]:
        sim.world.add_resource(cls(**kwargs))
        return cls

    return decorator


def system(sim: Neighborly, **kwargs: Any):
    """Add a class as a simulation system

    This decorator adds an instance of the decorated class as a shared resource.

    Parameters
    ----------
    sim: Neighborly
        The simulation instance to register the life event to
    **kwargs: Any
        Keyword arguments to pass to the constructor of the decorated class
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
    """
    Decorator that marks a function as a location bias rule

    Parameters
    ----------
    description: str
        Text description of the rule
    """

    def decorator(rule: ISocialRule):
        SocialRules.add(rule, description)
        return rule

    return decorator


def location_bias_rule(description: str):
    """
    Decorator that marks a function as a location bias rule

    Parameters
    ----------
    description: str
        Text description of the rule
    """

    def decorator(rule: ILocationBiasRule):
        LocationBiasRules.add(rule, description)

    return decorator


def event_listener(event_type: Optional[Type[Event]] = None):
    def decorator(listener: Callable[[GameObject, Event], None]) -> None:
        if event_type is None:
            GameObject.on_any(listener)
        else:
            GameObject.on(event_type, listener)

    return decorator
