"""
Utility decorators that should assist with content authoring
"""
from typing import Any, Type, TypeVar

from neighborly.content_management import (
    AIBrainFactory,
    AIBrainLibrary,
    LifeEventLibrary,
    LocationBiasRuleLibrary,
    SocialRuleLibrary,
)
from neighborly.core.ecs import Component, IComponentFactory, ISystem
from neighborly.core.life_event import ActionableLifeEvent
from neighborly.core.location_bias import ILocationBiasRule
from neighborly.core.social_rule import ISocialRule
from neighborly.simulation import Neighborly

_CT = TypeVar("_CT", bound=Component)
_CF = TypeVar("_CF", bound=IComponentFactory)
_RT = TypeVar("_RT", bound=Any)
_ST = TypeVar("_ST", bound=ISystem)
_LT = TypeVar("_LT", bound=ActionableLifeEvent)


def brain_factory(sim: Neighborly, name: str):
    def decorator(fn: AIBrainFactory):
        sim.world.get_resource(AIBrainLibrary).add(name, fn)
        return fn

    return decorator


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


def life_event(sim: Neighborly):
    """Add a class as a simulation system

    This decorator adds an instance of the decorated class as a shared resource.

    Parameters
    ----------
    sim: Neighborly
        The simulation instance to register the life event to
    """

    def decorator(cls: Type[_LT]) -> Type[_LT]:
        sim.world.get_resource(LifeEventLibrary).add(cls)
        return cls

    return decorator


def social_rule(sim: Neighborly, description: str = ""):
    def decorator(rule: ISocialRule):
        sim.world.get_resource(SocialRuleLibrary).add(rule, description)
        return rule

    return decorator


def location_bias_rule(sim: Neighborly, description: str = ""):
    def decorator(rule: ILocationBiasRule):
        sim.world.get_resource(LocationBiasRuleLibrary).add(rule, description)

    return decorator
