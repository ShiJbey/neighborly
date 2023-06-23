"""Default job requirement rules

This module contains definitions for job requirement rule functions
used to precondition when characters are allowed to hold a certain
occupation.

"""

from typing import Any

from neighborly.components.business import JobRequirementLibrary
from neighborly.components.character import Gender, GenderType
from neighborly.components.shared import Age
from neighborly.core.ecs import GameObject
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="default job requirements plugin",
    plugin_id="default.job_requirements",
    version="0.1.0",
)


def has_component(gameobject: GameObject, *args: Any) -> bool:
    component_name: str
    (component_name,) = args
    return gameobject.has_component(
        gameobject.world.get_component_info(component_name).component_type
    )


def has_gender(gameobject: GameObject, *args: Any) -> bool:
    gender_name: str
    (gender_name,) = args
    if gender := gameobject.try_component(Gender):
        return gender.gender == GenderType[gender_name]
    return False


def over_age(gameobject: GameObject, *args: Any) -> bool:
    years: float
    (years,) = args
    if age := gameobject.try_component(Age):
        return age.value > years
    return False


def setup(sim: Neighborly, **kwargs: Any):
    job_requirement_library = sim.world.get_resource(JobRequirementLibrary)
    job_requirement_library.add("has_component", has_component)
    job_requirement_library.add("has_gender", has_gender)
    job_requirement_library.add("over_age", over_age)
