"""Simulation inspection helper functions.

Tools and helper functions for inspecting simulations.

"""

from typing import Union

import tabulate

from neighborly.__version__ import VERSION
from neighborly.components.business import (
    Business,
    JobRole,
    Occupation,
    OpenForBusiness,
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
from neighborly.components.skills import Skill, Skills
from neighborly.components.traits import Trait, Traits
from neighborly.ecs import Active, GameObject
from neighborly.helpers.stats import get_stat
from neighborly.life_event import PersonalEventHistory
from neighborly.simulation import Simulation


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
        obj_ref = sim.world.gameobject_manager.get_gameobject(obj)
    else:
        obj_ref = obj

    if obj_ref.has_component(Settlement):
        inspect_settlement(obj_ref)
    elif obj_ref.has_component(District):
        inspect_district(obj_ref)
    elif obj_ref.has_component(Business):
        inspect_business(obj_ref)
    elif obj_ref.has_component(ResidentialBuilding):
        inspect_residence(obj_ref)
    elif obj_ref.has_component(ResidentialUnit):
        inspect_residential_unit(obj_ref)
    elif obj_ref.has_component(Character):
        inspect_character(obj_ref)
    elif obj_ref.has_component(Relationship):
        inspect_relationship(obj_ref)
    elif obj_ref.has_component(JobRole):
        inspect_job_role(obj_ref)
    elif obj_ref.has_component(Trait):
        inspect_trait(obj_ref)
    elif obj_ref.has_component(Skill):
        inspect_skill(obj_ref)
    else:
        inspect_general(obj_ref)


def inspect_settlement(settlement: GameObject) -> None:
    """Print information about a settlement."""

    settlement_data = settlement.get_component(Settlement)

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

    output = "\n"
    output += "Settlement\n"
    output += "==========\n"
    output += "\n"
    output += f"UID: {settlement.uid}\n"
    output += f"Name: {settlement_data.name}\n"
    output += f"Population: {settlement_data.population}\n"
    # output += f"description:\n{get_settlement_description(settlement_data)}\n"
    output += "\n"
    output += "=== Districts ===\n"
    output += f"{districts}\n"

    print(output)


def inspect_district(district: GameObject) -> None:
    """Print information about a district."""

    district_data = district.get_component(District)

    # if district_data.description == "":
    #     description = f"A district within {district_data.settlement.name}"
    # else:
    #     description = district_data.description

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

    output = "\n"
    output += "District\n"
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

    print(output)


def inspect_business(business: GameObject) -> None:
    """Print information about a business."""
    business_data = business.get_component(Business)

    employee_table = tabulate.tabulate(
        [
            (employee.name, role.gameobject.name)
            for employee, role in business_data.employees.items()
        ],
        headers=("Employee", "Role"),
    )

    activity_status = "active" if business.has_component(Active) else "inactive"

    event_history = _get_personal_history_table(
        business.get_component(PersonalEventHistory)
    )

    output = "\n"
    output += "Business\n"
    output += "========\n"
    output += "\n"
    output += f"UID: {business.uid}\n"
    output += f"Name: {business_data.name}\n"
    output += f"Status: {activity_status}\n"
    output += f"District: {business_data.district}\n"
    output += f"Owner: {business_data.owner}\n"
    output += f"Owner role: {business_data.owner_role.display_name}\n"
    output += "\n"
    output += "=== Employees ===\n"
    output += f"{employee_table}\n"
    output += "\n"
    output += "=== Traits ===\n"
    output += f"{_get_traits_table(business.get_component(Traits))}\n"
    output += "\n"
    output += "=== Frequented By ===\n"
    output += f"{_get_frequented_by_table(business.get_component(FrequentedBy))}\n"
    output += "\n"
    output += "=== Event History ===\n"
    output += f"{event_history}\n"
    output += "\n"

    print(output)


def inspect_residence(residence: GameObject) -> None:
    """Print information about a residence."""
    building_data = residence.get_component(ResidentialBuilding)

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

    output = "\n"
    output += "Residential Building\n"
    output += "====================\n"
    output += "\n"
    output += f"UID: {residence.uid}\n"
    output += f"Name: {residence.name}\n"
    output += f"Status: {activity_status}\n"
    output += f"District: {building_data.district}\n"
    output += "\n"
    output += "=== Traits ===\n"
    output += f"{_get_traits_table(residence.get_component(Traits))}\n"
    output += "\n"
    output += "=== Residential Units ===\n"
    output += f"{residential_units}\n"
    output += "\n"

    print(output)


def inspect_residential_unit(residential_unit: GameObject) -> None:
    """Print information about a unit within a residential building."""
    unit_data = residential_unit.get_component(ResidentialUnit)

    residents = ", ".join(r.name for r in unit_data.residents)

    output = "\n"
    output += "Residential Unit\n"
    output += "================\n"
    output += "\n"
    output += f"UID: {residential_unit.uid}\n"
    output += f"Name: {residential_unit.name}\n"
    output += f"Building: {unit_data.building.name}\n"
    output += f"District: {unit_data.district.name}\n"
    output += f"Residents: {residents}\n"
    output += "\n"

    print(output)


def inspect_character(character: GameObject) -> None:
    """Print information about a character."""
    character_data = character.get_component(Character)

    skills_table = tabulate.tabulate(
        [
            (skill.name, stat.value, skill.get_component(Skill).description)
            for skill, stat in character.get_component(Skills)
        ],
        headers=("Name", "Level", "Description"),
    )

    activity_status = "active" if character.has_component(Active) else "inactive"

    frequented_locations = tabulate.tabulate(
        [
            (entry.uid, entry.name)
            for entry in character.get_component(FrequentedLocations)
        ],
        headers=("UID", "Name"),
    )

    event_history = _get_personal_history_table(
        character.get_component(PersonalEventHistory)
    )

    residence = "N/A"
    if resident := character.try_component(Resident):
        residence = resident.residence.get_component(ResidentialUnit).building.name

    works_at = "N/A"
    if occupation := character.try_component(Occupation):
        works_at = occupation.business.name

    output = "\n"
    output += "Character\n"
    output += "=========\n"
    output += "\n"
    output += f"UID: {character.uid}\n"
    output += f"Name: {character_data.full_name}\n"
    output += f"Status: {activity_status}\n"
    output += f"Age: {int(character_data.age)}\n"
    output += f"Sex: {character_data.sex.name}\n"
    output += f"Species: {character_data.species.name}\n"
    output += "\n"
    output += f"Works at: {works_at}\n"
    output += f"Residence: {residence}\n"
    output += "\n"
    output += "=== Traits ===\n"
    output += f"{_get_traits_table(character.get_component(Traits))}\n"
    output += "\n"
    output += "=== Skills ===\n"
    output += f"{skills_table}\n"
    output += "\n"
    output += "=== Frequented Locations ===\n"
    output += f"{frequented_locations}\n"
    output += "\n"
    output += "=== Relationships ===\n"
    output += f"{_get_relationships_table(character.get_component(Relationships))}\n"
    output += "\n"
    output += "=== Event History ===\n"
    output += f"{event_history}\n"
    output += "\n"

    print(output)


def inspect_relationship(relationship: GameObject) -> None:
    """Print information about a relationship."""

    relationship_data = relationship.get_component(Relationship)

    reputation = get_stat(relationship, "reputation").value
    romance = get_stat(relationship, "romance").value
    compatibility = get_stat(relationship, "compatibility").value
    romantic_compatibility = get_stat(relationship, "romantic_compatibility").value
    interaction_score = get_stat(relationship, "interaction_score").value

    output = "\n"
    output += "Relationship\n"
    output += "============\n"
    output += "\n"
    output += f"UID: {relationship.uid}\n"
    output += f"Name: {relationship.name}\n"
    output += "\n"
    output += f"Owner: {relationship_data.owner.name}\n"
    output += f"Target: {relationship_data.target.name}\n"
    output += "\n"
    output += f"Reputation: {int(reputation)}\n"
    output += f"Romance: {int(romance)}\n"
    output += f"Compatibility: {compatibility}\n"
    output += f"Romantic Compatibility: {romantic_compatibility}\n"
    output += f"Interaction Score: {int(interaction_score)}\n"
    output += "\n"
    output += "=== Traits ===\n"
    output += f"{_get_traits_table(relationship.get_component(Traits))}\n"
    output += "\n"

    print(output)


def inspect_job_role(job_role: GameObject) -> None:
    """Print information about a job role."""

    job_role_data = job_role.get_component(JobRole)

    requirements = "\n".join(f"- {p.description}" for p in job_role_data.requirements)
    effects = "\n".join(f"- {e.description}" for e in job_role_data.effects)
    monthly_effects = "\n".join(
        f"- {e.description}" for e in job_role_data.monthly_effects
    )

    output = "\n"
    output += "Job Role\n"
    output += "========\n"
    output += "\n"
    output += f"UID: {job_role.uid}\n"
    output += f"Name: {job_role_data.display_name}\n"
    output += f"Definition ID: {job_role_data.definition_id}\n"
    output += f"Description:\n {job_role_data.description}\n"
    output += f"Job Level:\n {job_role_data.job_level}\n"
    output += "\n"
    output += "=== Requirements ===\n"
    output += f"{requirements}\n"
    output += "\n"
    output += "=== Effects ===\n"
    output += f"{effects}\n"
    output += "\n"
    output += "=== Monthly Effects ===\n"
    output += f"{monthly_effects}\n"
    output += "\n"
    output += "\n"

    print(output)


def inspect_trait(trait: GameObject) -> None:
    """Print information about a trait."""
    trait_data = trait.get_component(Trait)

    effects = "\n".join(f"- {e.description}" for e in trait_data.effects)
    conflicting_traits = ", ".join(t for t in trait_data.conflicting_traits)

    output = "\n"
    output += "Trait\n"
    output += "=====\n"
    output += "\n"
    output += f"UID: {trait.uid}\n"
    output += f"Name: {trait_data.display_name}\n"
    output += f"Definition ID: {trait_data.definition_id}\n"
    output += f"Description:\n{trait_data.description}\n"
    output += "\n"
    output += "=== Conflicting Trait Definitions ===\n"
    output += f"{conflicting_traits}\n"
    output += "\n"
    output += "=== Effects ===\n"
    output += f"{effects}\n"
    output += "\n"
    output += "\n"

    print(output)


def inspect_skill(skill: GameObject) -> None:
    """Print information about a skill."""
    skill_data = skill.get_component(Skill)

    output = "\n"
    output += "Skill\n"
    output += "=====\n"
    output += "\n"
    output += f"UID: {skill.uid}\n"
    output += f"Name: {skill_data.display_name}\n"
    output += f"Definition ID: {skill_data.definition_id}\n"
    output += f"Description:\n{skill_data.description}\n"
    output += "\n"

    print(output)


def inspect_general(obj: GameObject) -> None:
    """Print information about a GameObject."""
    component_debug_strings = "".join([f"\t{repr(c)}\n" for c in obj.get_components()])

    debug_str = (
        f"name: {obj.name}\n"
        f"uid: {obj.uid}\n"
        f"components: [\n{component_debug_strings}]"
    )

    print(debug_str)


def list_settlements(sim: Simulation) -> None:
    """Print the list of settlements in the simulation."""
    settlements = [
        (uid, settlement.name, settlement.population)
        for uid, (settlement, _) in sim.world.get_components((Settlement, Active))
    ]

    table = tabulate.tabulate(settlements, headers=["UID", "Name", "Population"])

    # Display as a table the object ID, Display Name, Description
    output = "\n"
    output += "=== Settlements ===\n"
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
    output = "\n"
    output += "=== Districts ===\n"
    output += table
    output += "\n"

    print(output)


def list_businesses(sim: Simulation, inactive_ok: bool = False) -> None:
    """Print businesses in the simulation."""
    if inactive_ok:
        businesses = [
            (
                uid,
                business.name,
                str(business.owner),
                business.district.name,
            )
            for uid, (business,) in sim.world.get_components((Business,))
        ]
    else:
        businesses = [
            (
                uid,
                business.name,
                str(business.owner),
                business.district.name,
            )
            for uid, (business, _) in sim.world.get_components(
                (Business, OpenForBusiness)
            )
        ]

    table = tabulate.tabulate(businesses, headers=["UID", "Name", "Owner", "District"])

    # Display as a table the object ID, Display Name, Description
    output = "\n"
    output += "=== Businesses ===\n"
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
                str(character.species.get_component(Trait).display_name),
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
    output = "\n"
    output += "=== Characters ===\n"
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
    output = "\n"
    output += "=== Residential Buildings ===\n"
    output += table
    output += "\n"

    print(output)


def list_job_roles(sim: Simulation) -> None:
    """List job roles instances from the simulation."""
    job_roles = [
        (uid, role.display_name, role.description)
        for uid, (role,) in sim.world.get_components((JobRole,))
    ]

    table = tabulate.tabulate(job_roles, headers=["UID", "Name", "Description"])

    # Display as a table the object ID, Display Name, Description
    output = "\n"
    output += "=== Job Roles ===\n"
    output += table
    output += "\n"

    print(output)


def list_traits(sim: Simulation) -> None:
    """List the trait instances from the simulation."""
    traits = [
        (uid, trait.display_name, trait.description)
        for uid, (trait,) in sim.world.get_components((Trait,))
    ]

    table = tabulate.tabulate(traits, headers=["UID", "Name", "Description"])

    # Display as a table the object ID, Display Name, Description
    output = "\n"
    output += "=== Traits ===\n"
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
    output = "\n"
    output += "=== Skills ===\n"
    output += table
    output += "\n"

    print(output)


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


def _get_frequented_by_table(frequented_by: FrequentedBy) -> str:
    """Generate a string table for a FrequentedBy component."""

    return tabulate.tabulate(
        [
            (entry.uid, entry.get_component(Character).full_name)
            for entry in frequented_by
        ],
        headers=("UID", "Name"),
    )


def _get_traits_table(traits: Traits) -> str:
    """Generate a string table for a Traits component."""

    return tabulate.tabulate(
        [
            (entry.name, entry.get_component(Trait).description)
            for entry in traits.traits
        ],
        headers=("Name", "Description"),
    )


def _get_personal_history_table(history: PersonalEventHistory) -> str:
    """Generate a string table for a PersonalEventHistory component."""
    event_data: list[tuple[str, str]] = [
        (str(event.timestamp), str(event)) for event in history.history
    ]

    return tabulate.tabulate(
        event_data,
        headers=("Timestamp", "Description"),
    )


def _get_relationships_table(relationships: Relationships) -> str:
    relationship_data: list[tuple[str, float, float, float, float, float, str]] = []

    for target, relationship in relationships.outgoing.items():
        reputation = get_stat(relationship, "reputation").value
        romance = get_stat(relationship, "romance").value
        compatibility = get_stat(relationship, "compatibility").value
        romantic_compatibility = get_stat(relationship, "romantic_compatibility").value
        interaction_score = get_stat(relationship, "interaction_score").value
        traits = ", ".join(t.name for t in relationship.get_component(Traits).traits)

        relationship_data.append(
            (
                target.name,
                int(reputation),
                int(romance),
                compatibility,
                romantic_compatibility,
                int(interaction_score),
                traits,
            )
        )

    return tabulate.tabulate(
        relationship_data,
        headers=(
            "Target",
            "Reputation",
            "Romance",
            "Compatibility",
            "Romantic Compatibility",
            "Interaction Score",
            "Traits",
        ),
    )
