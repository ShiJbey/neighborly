"""Content Loaders.

This module contains definitions of helper functions that load various
simulation data into a simulation.

"""

from __future__ import annotations

import os
from typing import Any, Type, Union

import yaml

from neighborly.components.location import LocationPreferenceRule
from neighborly.components.relationship import SocialRule
from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    JobRoleLibrary,
    LifeEventLibrary,
    LocationPreferenceLibrary,
    ResidenceLibrary,
    SettlementLibrary,
    SkillLibrary,
    SocialRuleLibrary,
    TraitLibrary,
)
from neighborly.life_event import LifeEvent
from neighborly.simulation import Simulation
from neighborly.tracery import Tracery


def load_districts(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load settlement district definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    file_path
        The path to the data file.
    """
    with open(file_path, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    district_library = sim.world.resource_manager.get_resource(DistrictLibrary)

    for district_id, params in data.items():
        district_library.add_definition_from_obj(
            {"definition_id": district_id, **params}
        )


def load_residences(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load residential building definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    file_path
        The path to the data file.
    """
    with open(file_path, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    residence_library = sim.world.resource_manager.get_resource(ResidenceLibrary)

    for residence_id, params in data.items():
        residence_library.add_definition_from_obj(
            {"definition_id": residence_id, **params}
        )


def load_settlements(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load settlement definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    file_path
        The path to the data file.
    """
    with open(file_path, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    settlement_library = sim.world.resource_manager.get_resource(SettlementLibrary)

    for settlement_id, params in data.items():
        settlement_library.add_definition_from_obj(
            {"definition_id": settlement_id, **params}
        )


def load_businesses(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load business definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    file_path
        The path to the data file.
    """
    with open(file_path, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    business_library = sim.world.resource_manager.get_resource(BusinessLibrary)

    for business_id, params in data.items():
        business_library.add_definition_from_obj(
            {"definition_id": business_id, **params}
        )


def load_job_roles(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load business definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    file_path
        The path to the data file.
    """
    with open(file_path, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    job_role_library = sim.world.resource_manager.get_resource(JobRoleLibrary)

    for entry_id, params in data.items():
        job_role_library.add_definition_from_obj({"definition_id": entry_id, **params})


def load_characters(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load character definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    file_path
        The path to the data file.
    """

    with open(file_path, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    character_library = sim.world.resource_manager.get_resource(CharacterLibrary)

    for character_id, params in data.items():
        character_library.add_definition_from_obj(
            {"definition_id": character_id, **params}
        )


def load_traits(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load trait definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    file_path
        The path to the data file.
    """

    with open(file_path, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    trait_library = sim.world.resource_manager.get_resource(TraitLibrary)

    for trait_id, params in data.items():
        trait_library.add_definition_from_obj({"definition_id": trait_id, **params})


def load_tracery(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Loads Tracery rules from a JSON file.

    Parameters
    ----------
    sim
        The simulation instance.
    file_path
        The path of the data file to load.
    """
    with open(file_path, "r", encoding="utf8") as file:
        rule_data: dict[str, list[str]] = yaml.safe_load(file)
        sim.world.resource_manager.get_resource(Tracery).add_rules(rule_data)


def load_skills(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load skill definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    file_path
        The path to the data file.
    """

    with open(file_path, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    library = sim.world.resource_manager.get_resource(SkillLibrary)

    for definition_id, params in data.items():
        library.add_definition_from_obj({"definition_id": definition_id, **params})


def load_social_rules(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load social rules from a file."""

    with open(file_path, "r", encoding="utf8") as file:
        data: list[dict[str, Any]] = yaml.safe_load(file)

    library = sim.world.resource_manager.get_resource(SocialRuleLibrary)

    for entry in data:
        rule = SocialRule.model_validate(entry)
        library.add_rule(rule)


def load_location_preferences(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load location preference rules from a file."""

    with open(file_path, "r", encoding="utf8") as file:
        data: list[dict[str, Any]] = yaml.safe_load(file)

    library = sim.world.resource_manager.get_resource(LocationPreferenceLibrary)

    for entry in data:
        rule = LocationPreferenceRule.model_validate(entry)
        library.add_rule(rule)


def register_life_event_type(
    sim: Simulation, agent_type: str, life_event_type: Type[LifeEvent]
) -> None:
    """Register a LifeEvent subtype with the simulation's library."""
    sim.world.resource_manager.get_resource(LifeEventLibrary).add_event_type(
        agent_type, life_event_type
    )
