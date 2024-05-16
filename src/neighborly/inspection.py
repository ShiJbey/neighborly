"""Simulation inspection helper functions.

Tools and helper functions for inspecting simulations.

"""

from typing import Callable, Union

import tabulate

from neighborly import __version__
from neighborly.components.business import Business, BusinessStatus, Occupation
from neighborly.components.character import Character, ResidentOf, Species
from neighborly.components.location import (
    CurrentDistrict,
    FrequentedLocations,
    Location,
)
from neighborly.components.relationship import Relationship, Relationships
from neighborly.components.settlement import District, Settlement
from neighborly.components.shared import Age
from neighborly.components.skills import SKILL_MAX_VALUE, Skills
from neighborly.components.stats import Stats
from neighborly.components.traits import Traits
from neighborly.ecs import Active, GameObject, GameObjectNotFoundError
from neighborly.helpers.stats import get_stat
from neighborly.libraries import JobRoleLibrary, SkillLibrary, TraitLibrary
from neighborly.life_event import PersonalEventHistory
from neighborly.simulation import Simulation


def _sign(num: Union[int, float]) -> str:
    """Get the sign of a number."""
    return "-" if num < 0 else "+"


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
        [(entry.name,) for entry in settlement_data.districts],
        headers=("Name"),
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

    locations_table = tabulate.tabulate(
        [(entry.name,) for entry in district_data.locations], headers=("Name",)
    )

    output = "District\n"
    output += "========\n"
    output += f"Name: {district_data.name}\n"
    output += "\n"
    output += "=== Locations ===\n"
    output += f"{locations_table}\n"
    output += "\n"

    return output


def _business_header(business: GameObject) -> str:
    """Print information about a business."""
    business_data = business.try_component(Business)

    if business_data is None:
        return ""

    employee_table = tabulate.tabulate(
        [
            (employee.name, role.name)
            for employee, role in business_data.employees.items()
        ],
        headers=("Employee", "Role"),
    )

    activity_status = business_data.status.name

    output = "Business\n"
    output += "========\n"
    output += "\n"
    output += f"UID: {business.uid}\n"
    output += f"Name: {business_data.name}\n"
    output += f"Status: {activity_status}\n"
    output += f"District: {business.get_component(CurrentDistrict).district.name}\n"
    output += f"Owner: {business_data.owner.name if business_data.owner else None}\n"
    output += f"Owner role: {business_data.owner_role.name}\n"
    output += "\n"
    output += "=== Employees ===\n"
    output += f"{employee_table}\n"
    output += "\n"

    return output


def _character_header(character: GameObject) -> str:
    """Print information about a character."""
    character_data = character.try_component(Character)

    if character_data is None:
        return ""

    activity_status = "active" if character.has_component(Active) else "inactive"

    residence = "N/A"
    if resident_of := character.try_component(ResidentOf):
        residence = resident_of.settlement.name

    works_at = "N/A"
    if occupation := character.try_component(Occupation):
        works_at = occupation.business.name

    age = character.get_component(Age).value

    output = "Character\n"
    output += "=========\n"
    output += "\n"
    output += f"UID: {character.uid}\n"
    output += f"Name: {character_data.full_name}\n"
    output += f"Status: {activity_status}\n"
    output += f"Age: {int(age)} ({character_data.life_stage.name})\n"
    output += f"Sex: {character_data.sex.name}\n"
    output += f"Species: {character.get_component(Species).species.name}\n"
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


def _get_frequented_by_table(obj: GameObject) -> str:
    """Generate a string table for a FrequentedBy component."""
    frequented_by = obj.try_component(Location)

    if frequented_by is None:
        return ""

    output = "=== Frequented By ===\n"

    output += tabulate.tabulate(
        [
            (entry.uid, entry.get_component(Character).full_name)
            for entry in frequented_by
        ],
        headers=("UID", "Name"),
    )

    output += "\n"

    return output


def _get_traits_table(obj: GameObject) -> str:
    """Generate a string table for a Traits component."""
    if not obj.has_component(Traits):
        return ""

    traits = obj.get_component(Traits)

    output = "=== Traits ===\n"

    output += tabulate.tabulate(
        [(entry.trait.name, entry.description) for entry in traits.traits.values()],
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

    relationship_data: list[tuple[bool, int, str, str, str, str]] = []

    for target, relationship in relationships.outgoing.items():
        reputation = get_stat(relationship, "reputation")
        romance = get_stat(relationship, "romance")
        traits = ", ".join(
            t.trait.name for t in relationship.get_component(Traits).traits.values()
        )
        rep_base = int(reputation.base_value)
        rom_base = int(romance.base_value)
        rep_boost = int(reputation.value - reputation.base_value)
        rom_boost = int(romance.value - romance.base_value)

        relationship_data.append(
            (
                relationship.has_component(Active),
                relationship.uid,
                target.name,
                f"{rep_base}[{_sign(rep_boost)}{abs(rep_boost)}]",
                f"{rom_base}[{_sign(rom_boost)}{abs(rom_boost)}]",
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
            "Reputation",
            "Romance",
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

    stats_table_data: list[tuple[str, str]] = []

    for stat_component in stats.stats:
        stat = stat_component.stat
        if stat.is_discrete:
            boost = int(stat.value - stat.base_value)
            value_label = f"{int(stat.base_value)}[{_sign(boost)}{abs(boost)}]"
        else:
            boost = int(stat.value - stat.base_value)
            value_label = f"{stat.base_value:.3f}[{_sign(boost)}{abs(boost)}]"

        stats_table_data.append((stat_component.stat_name, value_label))

    output = "=== Stats ===\n"
    output += tabulate.tabulate(
        stats_table_data, headers=("Stat", "Value"), numalign="left"
    )
    output += "\n"

    return output


def _get_skills_table(obj: GameObject) -> str:
    skill_data = obj.try_component(Skills)

    library = obj.world.resources.get_resource(SkillLibrary)

    if skill_data is None:
        return ""

    output = "=== Skills ===\n"
    output += tabulate.tabulate(
        [
            (
                skill_id,
                f"{int(skill.stat.value)}/{int(SKILL_MAX_VALUE)}",
                library.get_definition(skill_id).description,
            )
            for skill_id, skill in skill_data.skills.items()
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
    ("relationship", _relationship_header),
    ("business", _business_header),
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
    output += f"Simulation Version: {__version__}\n"

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
        (uid, district.name)
        for uid, (district, _) in sim.world.get_components((District, Active))
    ]

    table = tabulate.tabulate(districts, headers=["UID", "Name"])

    # Display as a table the object ID, Display Name, Description
    output = "=== Districts ===\n"
    output += table
    output += "\n"

    print(output)


def list_businesses(sim: Simulation, inactive_ok: bool = False) -> None:
    """Print businesses in the simulation."""

    businesses: list[tuple[str, ...]] = []

    for uid, (business,) in sim.world.get_components((Business,)):
        activity_status = business.status.name

        if business.status == BusinessStatus.OPEN or inactive_ok:
            businesses.append(
                (
                    str(uid),
                    business.name,
                    str(business.owner),
                    activity_status,
                    business.gameobject.get_component(CurrentDistrict).district.name,
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
                int(age.value),
                str(character.sex.name),
                str(species.species.name),
            )
            for uid, (character, species, age) in sim.world.get_components(
                (Character, Species, Age)
            )
        ]
    else:
        characters = [
            (
                uid,
                character.full_name,
                int(age.value),
                str(character.sex.name),
                str(species.species.name),
            )
            for uid, (character, species, age, _) in sim.world.get_components(
                (Character, Species, Age, Active)
            )
        ]

    table = tabulate.tabulate(
        characters, headers=["UID", "Name", "Age", "Sex", "Species"]
    )

    # Display as a table the object ID, Display Name, Description
    output = "=== Characters ===\n"
    output += table
    output += "\n"

    print(output)


def list_job_roles(sim: Simulation) -> None:
    """List job roles instances from the simulation."""

    job_role_library = sim.world.resources.get_resource(JobRoleLibrary)

    job_roles = [
        (role_def.definition_id, role_def.name, role_def.description)
        for role_def in job_role_library.definitions.values()
    ]

    table = tabulate.tabulate(job_roles, headers=["Role ID", "Name", "Description"])

    # Display as a table the object ID, Display Name, Description
    output = "=== Job Roles ===\n"
    output += table
    output += "\n"

    print(output)


def list_traits(sim: Simulation) -> None:
    """List the trait instances from the simulation."""

    trait_library = sim.world.resources.get_resource(TraitLibrary)

    traits = [
        (trait_def.definition_id, trait_def.name, trait_def.description)
        for trait_def in trait_library.instances.values()
    ]

    table = tabulate.tabulate(traits, headers=["Trait ID", "Name", "Description"])

    # Display as a table the object ID, Display Name, Description
    output = "=== Traits ===\n"
    output += table
    output += "\n"

    print(output)


def list_skills(sim: Simulation) -> None:
    """List all the potential skills in the simulation."""

    skill_library = sim.world.resources.get_resource(SkillLibrary)

    skills = [
        (skill_def.definition_id, skill_def.name, skill_def.description)
        for skill_def in skill_library.definitions.values()
    ]

    table = tabulate.tabulate(skills, headers=["Skill ID", "Name", "Description"])

    # Display as a table the object ID, Display Name, Description
    output = "=== Skills ===\n"
    output += table
    output += "\n"

    print(output)
