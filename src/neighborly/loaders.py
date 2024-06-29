"""Content Loaders.

This module contains definitions of helper functions that load various
simulation data into a simulation.

"""

from __future__ import annotations

import os
from typing import Any, Union

import yaml

from neighborly.defs.base_types import (
    BeliefDef,
    BusinessDef,
    CharacterDef,
    DistrictDef,
    JobRoleDef,
    SettlementDef,
    SkillDef,
    SpeciesDef,
    TraitDef,
)
from neighborly.libraries import (
    BeliefLibrary,
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    JobRoleLibrary,
    SettlementLibrary,
    SkillLibrary,
    SpeciesLibrary,
    TraitLibrary,
)
from neighborly.simulation import Simulation


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
        district_library.add_definition(
            DistrictDef.model_validate({"definition_id": district_id, **params})
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
        settlement_library.add_definition(
            SettlementDef.model_validate({"definition_id": settlement_id, **params})
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
        business_library.add_definition(
            BusinessDef.model_validate({"definition_id": business_id, **params})
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
        job_role_library.add_definition(
            JobRoleDef.model_validate({"definition_id": entry_id, **params})
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
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    character_library = sim.world.resource_manager.get_resource(CharacterLibrary)

    for character_id, params in data.items():
        character_library.add_definition(
            CharacterDef.model_validate({"definition_id": character_id, **params})
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
        trait_library.add_definition(
            TraitDef.model_validate({"definition_id": trait_id, **params})
        )


def load_species(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load species definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    file_path
        The path to the data file.
    """

    with open(file_path, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    library = sim.world.resource_manager.get_resource(SpeciesLibrary)

    for definition_id, params in data.items():
        library.add_definition(
            SpeciesDef.model_validate({"definition_id": definition_id, **params})
        )


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
        library.add_definition(
            SkillDef.model_validate({"definition_id": definition_id, **params})
        )


def load_beliefs(
    sim: Simulation, file_path: Union[os.PathLike[str], str, bytes]
) -> None:
    """Load beliefs from a file."""

    with open(file_path, "r", encoding="utf8") as file:
        data: list[dict[str, Any]] = yaml.safe_load(file)

    library = sim.world.resource_manager.get_resource(BeliefLibrary)

    for entry in data:
        library.add_definition(BeliefDef.model_validate(entry))
