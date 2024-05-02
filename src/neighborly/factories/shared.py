"""Factories for shared components.

"""

import random
from typing import Any

from neighborly.components.shared import Age, Agent
from neighborly.ecs import Component, ComponentFactory, World
from neighborly.life_event import PersonalEventHistory


class AgeFactory(ComponentFactory):
    """Creates Age component instances."""

    __component__ = "Age"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        rng = world.resources.get_resource(random.Random)

        value = kwargs.get("value", 0)

        if value_range := kwargs.get("value_range", ""):
            min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
            value = rng.randint(min_value, max_value)

        return Age(value=value)


class AgentFactory(ComponentFactory):
    """Creates Agent component instances."""

    __component__ = "Agent"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return Agent(agent_type=kwargs["agent_type"])


class PersonalEventHistoryFactory(ComponentFactory):
    """Creates PersonalEventHistory component instances."""

    __component__ = "PersonalEventHistory"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:
        return PersonalEventHistory()
