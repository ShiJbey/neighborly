"""Simulation inspection helper functions.

Tools and helper functions for inspecting simulations.

"""

from typing import Callable, Union

import tabulate

from neighborly.__version__ import VERSION
from neighborly.components.business import (
    Business,
    ClosedForBusiness,
    JobRole,
    Occupation,
    OpenForBusiness,
    PendingOpening,
)
from neighborly.components.character import Character
from neighborly.components.location import FrequentedBy, FrequentedLocations
from neighborly.components.relationship import Relationship, Relationships
from neighborly.components.residence import (
    Resident,
    ResidentialBuilding,
    ResidentialUnit,
)
from neighborly.components.settlement import District, Settlement
from neighborly.components.skills import SKILL_MAX_VALUE, Skill, Skills
from neighborly.components.stats import Stats
from neighborly.components.traits import Trait, Traits
from neighborly.ecs import Active, GameObject, GameObjectNotFoundError
from neighborly.helpers.stats import get_stat
from neighborly.life_event import PersonalEventHistory
from neighborly.simulation import Simulation


def _title_section(obj: GameObject) -> str:
    """Return string output for the section containing general GameObject data."""

    name_line = f"|| {obj.name} ||"
    frame_top_bottom = "=" * len(name_line)

    output = f"{frame_top_bottom}\n"
    output += f"{name_line}\n"
    output += f"{frame_top_bottom}\n\n"

    return output


def _settlement_section(obj: GameObject) -> str:
    """Return string output for a section focuses on settlement data."""
    if obj.has_component(Settlement) is False:
        return ""

    settlement_data = obj.get_component(Settlement)

    districts = tabulate.tabulate(
        [
            (
                entry.uid,
                entry.get_component(District).name,
                entry.get_component(District).population,
            )
            for entry in settlement_data.districts
        ],
        headers=("UID", "Name", "Population"),
    )

    output = ""
    output += "Settlement\n"
    output += "==========\n"
    output += "\n"
    output += f"Name: {settlement_data.name}\n"
    output += f"Population: {settlement_data.population}\n"
    output += "\n"
    output += "=== Districts ===\n"
    output += f"{districts}\n"

    return output


def _district_header(district: GameObject) -> str:
    """Print information about a district."""

    district_data = district.try_component(District)

    if district_data is None:
        return ""

    residential_buildings_table = tabulate.tabulate(
        [(entry.name,) for entry in district_data.residences], headers=("Name",)
    )

    businesses_table = tabulate.tabulate(
        [(entry.name,) for entry in district_data.businesses], headers=("Name",)
    )

    resident_data: list[tuple[int, str]] = []
    for entry in district_data.residences:
        building = entry.get_component(ResidentialBuilding)
        for unit in building.units:
            residents = unit.get_component(ResidentialUnit).residents
            for resident in residents:
                resident_data.append(
                    (resident.uid, resident.get_component(Character).full_name)
                )

    residents_table = tabulate.tabulate(resident_data, headers=("UID", "Name"))

    output = "District\n"
    output += "========\n"
    output += "\n"
    output += f"UID: {district.uid}\n"
    output += f"Name: {district_data.name}\n"
    output += f"Population: {district_data.population}\n"
    # output += f"description\n: {description}\n"
    output += "\n"
    output += "=== Residential Buildings ===\n"
    output += f"{residential_buildings_table}\n"
    output += "\n"
    output += "=== Businesses ===\n"
    output += f"{businesses_table}\n"
    output += "\n"
    output += "=== Residents ===\n"
    output += f"{residents_table}\n"
    output += "\n"

    return output


def _business_header(business: GameObject) -> str:
    """Print information about a business."""
    business_data = business.try_component(Business)

    if business_data is None:
        return ""

    employee_table = tabulate.tabulate(
        [
            (employee.name, role.gameobject.name)
            for employee, role in business_data.employees.items()
        ],
        headers=("Employee", "Role"),
    )

    activity_status = "inactive"
    if business.has_component(OpenForBusiness):
        activity_status = "open-for-business"
    elif business.has_component(PendingOpening):
        activity_status = "looking for owner"
    elif business.has_component(ClosedForBusiness):
        activity_status = "closed-for-business"

    output = "Business\n"
    output += "========\n"
    output += "\n"
    output += f"UID: {business.uid}\n"
    output += f"Name: {business_data.name}\n"
    output += f"Status: {activity_status}\n"
    output += f"District: {business_data.district}\n"
    output += f"Owner: {business_data.owner.name if business_data.owner else None}\n"
    output += f"Owner role: {business_data.owner_role.definition.display_name}\n"
    output += "\n"
    output += "=== Employees ===\n"
    output += f"{employee_table}\n"
    output += "\n"

    return output


def _residential_building_header(residence: GameObject) -> str:
    """Print information about a residence."""
    building_data = residence.try_component(ResidentialBuilding)

    if building_data is None:
        return ""

    activity_status = "active" if residence.has_component(Active) else "inactive"

    residential_units = tabulate.tabulate(
        [
            (
                entry.uid,
                ", ".join(
                    r.name for r in entry.get_component(ResidentialUnit).residents
                ),
            )
            for entry in building_data.units
        ],
        headers=("Unit", "Residents"),
    )

    output = "Residential Building\n"
    output += "====================\n"
    output += "\n"
    output += f"UID: {residence.uid}\n"
    output += f"Name: {residence.name}\n"
    output += f"Status: {activity_status}\n"
    output += f"District: {building_data.district}\n"
    output += "\n"
    output += "=== Residential Units ===\n"
    output += f"{residential_units}\n"
    output += "\n"

    return output


def _residential_unit_header(residential_unit: GameObject) -> str:
    """Print information about a unit within a residential building."""
    unit_data = residential_unit.try_component(ResidentialUnit)

    if unit_data is None:
        return ""

    residents = ", ".join(r.name for r in unit_data.residents)

    output = "Residential Unit\n"
    output += "================\n"
    output += "\n"
    output += f"UID: {residential_unit.uid}\n"
    output += f"Name: {residential_unit.name}\n"
    output += f"Building: {unit_data.building.name}\n"
    output += f"District: {unit_data.district.name}\n"
    output += f"Residents: {residents}\n"
    output += "\n"

    return output


def _character_header(character: GameObject) -> str:
    """Print information about a character."""
    character_data = character.try_component(Character)

    if character_data is None:
        return ""

    activity_status = "active" if character.has_component(Active) else "inactive"

    residence = "N/A"
    if resident := character.try_component(Resident):
        residence = resident.residence.get_component(ResidentialUnit).building.name

    works_at = "N/A"
    if occupation := character.try_component(Occupation):
        works_at = occupation.business.name

    output = "Character\n"
    output += "=========\n"
    output += "\n"
    output += f"UID: {character.uid}\n"
    output += f"Name: {character_data.full_name}\n"
    output += f"Status: {activity_status}\n"
    output += f"Age: {int(character_data.age)} ({character_data.life_stage.name})\n"
    output += f"Sex: {character_data.sex.name}\n"
    output += f"Species: {character_data.species.name}\n"
    output += "\n"
    output += f"Works at: {works_at}\n"
    output += f"Residence: {residence}\n"
    output += "\n"

    return output


def _relationship_header(relationship: GameObject) -> str:
    """Print information about a relationship."""

    relationship_data = relationship.try_component(Relationship)

    if relationship_data is None:
        return ""

    output = "Relationship\n"
    output += "============\n"
    output += "\n"
    output += f"UID: {relationship.uid}\n"
    output += f"Name: {relationship.name}\n"
    output += "\n"
    output += f"Owner: {relationship_data.owner.name}\n"
    output += f"Target: {relationship_data.target.name}\n"

    return output


def _job_role_section(job_role: GameObject) -> str:
    """Print information about a job role."""
    if job_role.has_component(JobRole) is False:
        return ""

    job_role_data = job_role.get_component(JobRole)

    requirements = "\n".join(job_role_data.definition.requirements)

    output = "Job Role\n"
    output += "========\n"
    output += "\n"
    output += f"UID: {job_role.uid}\n"
    output += f"Name: {job_role_data.definition.display_name}\n"
    output += f"Definition ID: {job_role_data.definition_id}\n"
    output += f"Description:\n {job_role_data.definition.description}\n"
    output += f"Job Level:\n {job_role_data.definition.job_level}\n"
    output += "\n"
    output += "=== Requirements ===\n"
    output += f"{requirements}\n"
    output += "\n"

    return output


def _trait_section(trait: GameObject) -> str:
    """Print information about a trait."""
    if trait.has_component(Trait) is False:
        return ""

    trait_data = trait.get_component(Trait)

    conflicting_traits = ", ".join(t for t in trait_data.definition.conflicts_with)

    output = "Trait\n"
    output += "=====\n"
    output += "\n"
    output += f"UID: {trait.uid}\n"
    output += f"Name: {trait_data.definition.name}\n"
    output += f"Definition ID: {trait_data.definition_id}\n"
    output += f"Description:\n{trait_data.definition.description}\n"
    output += "\n"
    output += "=== Conflicting Trait Definitions ===\n"
    output += f"{conflicting_traits}\n"
    output += "\n"

    return output


def _skill_section(obj: GameObject) -> str:
    """Print information about a skill."""
    if obj.has_component(Skill) is False:
        return ""

    skill_data = obj.get_component(Skill)

    output = "Skill\n"
    output += "=====\n"
    output += "\n"
    output += f"UID: {obj.uid}\n"
    output += f"Name: {skill_data.display_name}\n"
    output += f"Definition ID: {skill_data.definition_id}\n"
    output += f"Description:\n{skill_data.description}\n"

    return output


def get_settlement_description(settlement: Settlement) -> str:
    """Create a string description of the settlement.

    Parameters
    ----------
    settlement
        The settlement to describe.

    Returns
    -------
    str
        The description.
    """
    districts = list(settlement.districts)

    concatenated_district_names = ", ".join([d.name for d in districts])

    description = (
        f"{settlement.name} has a population of {settlement.population}. "
        f"It has {len(districts)} district(s) ({concatenated_district_names})."
    )

    for district in districts:
        description += (
            f"{district.name} is {district.get_component(District).description}. "
        )

    return description


def _get_frequented_by_table(obj: GameObject) -> str:
    """Generate a string table for a FrequentedBy component."""
    frequented_by = obj.try_component(FrequentedBy)

    if frequented_by is None:
        return ""

    return tabulate.tabulate(
        [
            (entry.uid, entry.get_component(Character).full_name)
            for entry in frequented_by
        ],
        headers=("UID", "Name"),
    )


def _get_traits_table(obj: GameObject) -> str:
    """Generate a string table for a Traits component."""
    if not obj.has_component(Traits):
        return ""

    traits = obj.get_component(Traits)

    output = "=== Traits ===\n"

    output += tabulate.tabulate(
        [(entry.trait_id, entry.description) for entry in traits.traits.values()],
        headers=("Name", "Description"),
    )

    output += "\n"

    return output


def _get_personal_history_table(obj: GameObject) -> str:
    """Generate a string table for a PersonalEventHistory component."""
    history = obj.try_component(PersonalEventHistory)

    if history is None:
        return ""

    event_data: list[tuple[str, str]] = [
        (str(event.timestamp), str(event)) for event in history.history
    ]

    output = "=== Event History ===\n"
    output += tabulate.tabulate(
        event_data,
        headers=("Timestamp", "Description"),
    )
    output += "\n"

    return output


def _get_relationships_table(obj: GameObject) -> str:
    relationships = obj.try_component(Relationships)

    if relationships is None:
        return ""

    relationship_data: list[
        tuple[bool, int, str, float, float, float, float, float, str]
    ] = []

    for target, relationship in relationships.outgoing.items():
        reputation = get_stat(relationship, "reputation").value
        romance = get_stat(relationship, "romance").value
        compatibility = get_stat(relationship, "compatibility").value
        romantic_compatibility = get_stat(relationship, "romantic_compatibility").value
        interaction_score = get_stat(relationship, "interaction_score").value
        traits = ", ".join(
            t.trait_id for t in relationship.get_component(Traits).traits.values()
        )

        relationship_data.append(
            (
                relationship.has_component(Active),
                relationship.uid,
                target.name,
                int(reputation),
                int(romance),
                compatibility,
                romantic_compatibility,
                int(interaction_score),
                traits,
            )
        )

    output = "=== Relationships ===\n"
    output += tabulate.tabulate(
        relationship_data,
        headers=(
            "Active",
            "UID",
            "Target",
            "Rep.",
            "Rom.",
            "Compat.",
            "Rom. Compat.",
            "Int. Score",
            "Traits",
        ),
    )
    output += "\n"

    return output


def _get_stats_table(obj: GameObject) -> str:
    """Generate a table for stats."""
    stats = obj.try_component(Stats)

    if stats is None:
        return ""

    stats_table_data: list[tuple[str, str, str]] = []

    for stat_id, stat in stats:
        if stat.is_discrete:
            value_label = f"{int(stat.value)}"
        else:
            value_label = f"{stat.value:.3f}"

        if stat.is_bounded:
            min_value, max_value = stat.bounds
            if stat.is_discrete:
                min_max_label = f"[{int(min_value)}, {int(max_value)}]"
            else:
                min_max_label = f"[{min_value:.3f}, {max_value:.3f}]"
        else:
            min_max_label = "N/A"

        stats_table_data.append((stat_id, value_label, min_max_label))

    output = "=== Stats ===\n"
    output += tabulate.tabulate(
        stats_table_data, headers=("Stat", "Value", "Min/Max"), numalign="left"
    )
    output += "\n"

    return output


def _get_skills_table(obj: GameObject) -> str:
    skill_data = obj.try_component(Skills)

    if skill_data is None:
        return ""

    output = "=== Skills ===\n"
    output += tabulate.tabulate(
        [
            (
                entry.skill.gameobject.name,
                f"{int(entry.stat.value)}/{int(SKILL_MAX_VALUE)}",
                entry.skill.definition.description,
            )
            for entry in skill_data.skills.values()
        ],
        headers=("Name", "Level", "Description"),
    )
    output += "\n"
    return output


def _get_frequented_locations_table(obj: GameObject) -> str:
    frequented_locations = obj.try_component(FrequentedLocations)

    if frequented_locations is None:
        return ""

    output = "=== Frequented Locations ===\n"
    output += tabulate.tabulate(
        [(entry.uid, entry.name) for entry in frequented_locations],
        headers=("UID", "Name"),
    )

    output += "\n"

    return output


_obj_inspector_sections: list[tuple[str, Callable[[GameObject], str]]] = [
    ("title", _title_section),
    ("settlement", _settlement_section),
    ("district", _district_header),
    ("skill", _skill_section),
    ("trait", _trait_section),
    ("relationship", _relationship_header),
    ("residential_building", _residential_building_header),
    ("residential_unit", _residential_unit_header),
    ("business", _business_header),
    ("job_role", _job_role_section),
    ("character", _character_header),
    ("stats", _get_stats_table),
    ("traits", _get_traits_table),
    ("skills", _get_skills_table),
    ("frequented_by", _get_frequented_by_table),
    ("frequented_locations", _get_frequented_locations_table),
    ("relationships", _get_relationships_table),
    ("personal_history", _get_personal_history_table),
]
"""Static data containing functions that print various inspector sections."""


def add_inspector_section_fn(
    section_name: str, section_fn: Callable[[GameObject], str], after: str = ""
) -> None:
    """Add a function that generates a section of inspector output.

    Parameters
    ----------
    section_name
        The name of the section (used internally for ordering sections)
    section_fn
        A callable that prints the output of the section
    after
        The name of the section that this section should follow (defaults to "")
    """
    if after == "":
        _obj_inspector_sections.append((section_name, section_fn))
        return

    index = 0
    while index < len(_obj_inspector_sections):
        if _obj_inspector_sections[index][0] == after:
            break
        index += 1

    _obj_inspector_sections.insert(index + 1, (section_name, section_fn))


def print_sim_status(sim: Simulation) -> None:
    """Print the current status of the simulation."""

    output = ""
    output += "Simulation Status\n"
    output += "=================\n"
    output += "\n"
    output += f"World seed: {sim.config.seed}\n"
    output += f"World date: month {sim.date.month} of year {sim.date.year}\n"
    output += f"Simulation Version: {VERSION}\n"

    print(output)

    list_settlements(sim)
    list_districts(sim)


def inspect(sim: Simulation, obj: Union[int, GameObject]) -> None:
    """Print information about a GameObject.

    Parameters
    ----------
    sim
        A simulation instance.
    obj
        The GameObject instance or ID to inspect.
    """
    if isinstance(obj, int):
        try:
            obj_ref = sim.world.gameobject_manager.get_gameobject(obj)
        except GameObjectNotFoundError:
            print(f"No GameObject exists with the ID: {obj}.")
            return
    else:
        obj_ref = obj

    section_output: list[str] = []

    for _, section_fn in _obj_inspector_sections:
        section_str = section_fn(obj_ref)
        if section_str:
            section_output.append(section_str)

    combined_output = "\n\n".join(section_output)

    print(combined_output)


def list_settlements(sim: Simulation) -> None:
    """Print the list of settlements in the simulation."""
    settlements = [
        (uid, settlement.name, settlement.population)
        for uid, (settlement, _) in sim.world.get_components((Settlement, Active))
    ]

    table = tabulate.tabulate(settlements, headers=["UID", "Name", "Population"])

    # Display as a table the object ID, Display Name, Description
    output = "=== Settlements ===\n"
    output += table
    output += "\n"

    print(output)


def list_districts(sim: Simulation) -> None:
    """Prints the list of districts in the simulation."""
    districts = [
        (uid, district.name, district.settlement.name, district.population)
        for uid, (district, _) in sim.world.get_components((District, Active))
    ]

    table = tabulate.tabulate(
        districts, headers=["UID", "Name", "Settlement", "Population"]
    )

    # Display as a table the object ID, Display Name, Description
    output = "=== Districts ===\n"
    output += table
    output += "\n"

    print(output)


def list_businesses(sim: Simulation, inactive_ok: bool = False) -> None:
    """Print businesses in the simulation."""

    businesses: list[tuple[str, ...]] = []

    for uid, (business,) in sim.world.get_components((Business,)):
        activity_status = "inactive"
        if business.gameobject.has_component(OpenForBusiness):
            activity_status = "open-for-business"
        elif business.gameobject.has_component(PendingOpening):
            activity_status = "looking for owner"
        elif business.gameobject.has_component(ClosedForBusiness):
            activity_status = "closed-for-business"

        if business.gameobject.has_component(OpenForBusiness) or inactive_ok:
            businesses.append(
                (
                    str(uid),
                    business.name,
                    str(business.owner),
                    activity_status,
                    business.district.name,
                )
            )

    table = tabulate.tabulate(
        businesses, headers=["UID", "Name", "Owner", "Status", "District"]
    )

    # Display as a table the object ID, Display Name, Description
    output = "=== Businesses ===\n"
    output += table
    output += "\n"

    print(output)


def list_characters(sim: Simulation, inactive_ok: bool = False) -> None:
    """Print a list of characters from the simulation."""
    if inactive_ok:
        characters = [
            (
                uid,
                character.full_name,
                int(character.age),
                str(character.sex.name),
                str(character.species.name),
            )
            for uid, (character,) in sim.world.get_components((Character,))
        ]
    else:
        characters = [
            (
                uid,
                character.full_name,
                int(character.age),
                str(character.sex),
                str(character.species),
            )
            for uid, (character, _) in sim.world.get_components((Character, Active))
        ]

    table = tabulate.tabulate(
        characters, headers=["UID", "Name", "Age", "Sex", "Species"]
    )

    # Display as a table the object ID, Display Name, Description
    output = "=== Characters ===\n"
    output += table
    output += "\n"

    print(output)


def list_residences(sim: Simulation) -> None:
    """Print active residential buildings in the simulation."""
    residential_buildings = [
        (uid, building.gameobject.name, building.district.name)
        for uid, (building, _) in sim.world.get_components(
            (ResidentialBuilding, Active)
        )
    ]

    table = tabulate.tabulate(
        residential_buildings, headers=["UID", "Name", "District"]
    )

    # Display as a table the object ID, Display Name, Description
    output = "=== Residential Buildings ===\n"
    output += table
    output += "\n"

    print(output)


def list_job_roles(sim: Simulation) -> None:
    """List job roles instances from the simulation."""
    job_roles = [
        (uid, role.definition.display_name, role.definition.description)
        for uid, (role,) in sim.world.get_components((JobRole,))
    ]

    table = tabulate.tabulate(job_roles, headers=["UID", "Name", "Description"])

    # Display as a table the object ID, Display Name, Description
    output = "=== Job Roles ===\n"
    output += table
    output += "\n"

    print(output)


def list_traits(sim: Simulation) -> None:
    """List the trait instances from the simulation."""
    traits = [
        (uid, trait.definition.name, trait.definition.description)
        for uid, (trait,) in sim.world.get_components((Trait,))
    ]

    table = tabulate.tabulate(traits, headers=["UID", "Name", "Description"])

    # Display as a table the object ID, Display Name, Description
    output = "=== Traits ===\n"
    output += table
    output += "\n"

    print(output)


def list_skills(sim: Simulation) -> None:
    """List all the potential skills in the simulation."""

    skills = [
        (uid, skill.display_name, skill.description)
        for uid, (skill,) in sim.world.get_components((Skill,))
    ]

    table = tabulate.tabulate(skills, headers=["UID", "Name", "Description"])

    # Display as a table the object ID, Display Name, Description
    output = "=== Skills ===\n"
    output += table
    output += "\n"

    print(output)
