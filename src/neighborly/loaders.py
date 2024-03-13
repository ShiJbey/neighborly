"""Content Loaders.

This module contains definitions of helper functions that load various
simulation data into a simulation.

"""

from __future__ import annotations

import json
import os
from typing import Any, Union, cast

import pydantic
import yaml

from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    JobRoleLibrary,
    ResidenceLibrary,
    SettlementLibrary,
    SkillLibrary,
    TraitLibrary,
)
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
        data = yaml.safe_load(file)

    district_library = sim.world.resources.get_resource(DistrictLibrary)

    # This is a single definition
    if isinstance(data, dict):
        district_library.add_definition_from_obj(cast(dict[str, Any], data))

    # This is a list of definitions
    elif isinstance(data, list):
        data = cast(list[dict[str, Any]], data)
        for entry in data:
            district_library.add_definition_from_obj(entry)

    # This condition should never be reached, but this is here as a sanity check.
    else:
        raise TypeError(
            f"Unrecognized data type {type(data)} when loading {file_path!r}"
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
        data = yaml.safe_load(file)

    residence_library = sim.world.resources.get_resource(ResidenceLibrary)

    # This is a single definition
    if isinstance(data, dict):
        residence_library.add_definition_from_obj(cast(dict[str, Any], data))

    # This is a list of definitions
    elif isinstance(data, list):
        data = cast(list[dict[str, Any]], data)
        for entry in data:
            residence_library.add_definition_from_obj(entry)

    # This condition should never be reached, but this is here as a sanity check.
    else:
        raise TypeError(
            f"Unrecognized data type {type(data)} when loading {file_path!r}"
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
        data = yaml.safe_load(file)

    settlement_library = sim.world.resources.get_resource(SettlementLibrary)

    # This is a single definition
    if isinstance(data, dict):
        settlement_library.add_definition_from_obj(cast(dict[str, Any], data))

    # This is a list of definitions
    elif isinstance(data, list):
        data = cast(list[dict[str, Any]], data)
        for entry in data:
            settlement_library.add_definition_from_obj(entry)

    # This condition should never be reached, but this is here as a sanity check.
    else:
        raise TypeError(
            f"Unrecognized data type {type(data)} when loading {file_path!r}"
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
        data = yaml.safe_load(file)

    business_library = sim.world.resources.get_resource(BusinessLibrary)

    # This is a single definition
    if isinstance(data, dict):
        business_library.add_definition_from_obj(cast(dict[str, Any], data))

    # This is a list of definitions
    elif isinstance(data, list):
        data = cast(list[dict[str, Any]], data)
        for entry in data:
            business_library.add_definition_from_obj(entry)

    # This condition should never be reached, but this is here as a sanity check.
    else:
        raise TypeError(
            f"Unrecognized data type {type(data)} when loading {file_path!r}"
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
        data = yaml.safe_load(file)

    job_role_library = sim.world.resources.get_resource(JobRoleLibrary)

    # This is a single definition
    if isinstance(data, dict):
        job_role_library.add_definition_from_obj(cast(dict[str, Any], data))

    # This is a list of definitions
    elif isinstance(data, list):
        data = cast(list[dict[str, Any]], data)
        for entry in data:
            job_role_library.add_definition_from_obj(entry)

    # This condition should never be reached, but this is here as a sanity check.
    else:
        raise TypeError(
            f"Unrecognized data type {type(data)} when loading {file_path!r}"
        )


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
        data = yaml.safe_load(file)

    character_library = sim.world.resources.get_resource(CharacterLibrary)

    # This is a single definition
    if isinstance(data, dict):
        character_library.add_definition_from_obj(cast(dict[str, Any], data))

    # This is a list of definitions
    elif isinstance(data, list):
        data = cast(list[dict[str, Any]], data)
        for entry in data:
            character_library.add_definition_from_obj(entry)

    # This condition should never be reached, but this is here as a sanity check.
    else:
        raise TypeError(
            f"Unrecognized data type {type(data)} when loading {file_path!r}"
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
        data = yaml.safe_load(file)

    trait_library = sim.world.resources.get_resource(TraitLibrary)

    # This is a single definition
    if isinstance(data, dict):
        trait_library.add_definition_from_obj(cast(dict[str, Any], data))

    # This is a list of definitions
    elif isinstance(data, list):
        data = cast(list[dict[str, Any]], data)
        for entry in data:
            trait_library.add_definition_from_obj(entry)

    # This condition should never be reached, but this is here as a sanity check.
    else:
        raise TypeError(
            f"Unrecognized data type {type(data)} when loading {file_path!r}"
        )


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
        sim.world.resources.get_resource(Tracery).add_rules(rule_data)


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
        data = yaml.safe_load(file)

    skill_library = sim.world.resources.get_resource(SkillLibrary)

    # This is a single definition
    if isinstance(data, dict):
        try:
            skill_library.add_definition_from_obj(cast(dict[str, Any], data))
        except pydantic.ValidationError as err:
            raise RuntimeError(
                f"""
                Error while parsing skill definition: {err}.
                {json.dumps(data, indent=2)}
                """
            ) from err

    # This is a list of definitions
    elif isinstance(data, list):
        data = cast(list[dict[str, Any]], data)
        for entry in data:
            try:
                skill_library.add_definition_from_obj(entry)
            except pydantic.ValidationError as err:
                raise RuntimeError(
                    f"""
                    Error while parsing skill definition: {err}.
                    {json.dumps(data, indent=2)}
                    """
                ) from err

    # This condition should never be reached, but this is here as a sanity check.
    else:
        raise TypeError(
            f"Unrecognized data type {type(data)} when loading {file_path!r}"
        )
