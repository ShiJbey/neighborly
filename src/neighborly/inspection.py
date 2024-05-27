"""Simulation inspection helper functions.

Tools and helper functions for inspecting simulations.

"""

from typing import Callable, Union

import tabulate

from neighborly import __version__
from neighborly.components.beliefs import AppliedBeliefs, HeldBeliefs
from neighborly.components.business import (
    Business,
    BusinessStatus,
    Occupation,
    Unemployed,
)
from neighborly.components.character import (
    Character,
    Household,
    MemberOfHousehold,
    Pregnant,
    ResidentOf,
    Species,
)
from neighborly.components.location import (
    CurrentDistrict,
    FrequentedLocations,
    Location,
    LocationPreferences,
)
from neighborly.components.relationship import Relationship, Relationships
from neighborly.components.settlement import District, Settlement
from neighborly.components.shared import Age
from neighborly.components.skills import SKILL_MAX_VALUE, Skills
from neighborly.components.stats import Stats
from neighborly.components.traits import Traits, TraitType
from neighborly.ecs import Active, GameObject, GameObjectNotFoundError
from neighborly.helpers.stats import get_stat
from neighborly.libraries import (
    BeliefLibrary,
    JobRoleLibrary,
    LocationPreferenceLibrary,
    SkillLibrary,
    SpeciesLibrary,
    TraitLibrary,
)
from neighborly.life_event import PersonalEventHistory
from neighborly.simulation import Simulation


def _sign(num: Union[int, float]) -> str:
    """Get the sign of a number."""
    return "-" if num < 0 else "+"


def _title_section(obj: GameObject) -> str:
    """Return string output for the section containing general GameObject data."""

    name_line = f"|| {obj.name} ||"
    frame_top_bottom = "=" * len(name_line)

    output = [
        frame_top_bottom,
        name_line,
        frame_top_bottom,
        "",
        f"Active: {obj.is_active}",
        f"Name: {obj.name}",
    ]

    return "\n".join(output)


def _settlement_section(obj: GameObject) -> str:
    """Return string output for a section focuses on settlement data."""
    settlement = obj.try_component(Settlement)

    if settlement is None:
        return ""

    output = [
        "=== Settlement ===",
        "",
        f"Name: {settlement.name!r}",
        f"Population: {settlement.population}",
    ]

    if settlement.districts:
        output.append(f"Districts: (Total {len(settlement.districts)})")
        for district in settlement.districts:
            output.append(f"\t- {district.name}")
    else:
        output.append("Districts: None")

    return "\n".join(output)


def _district_section(obj: GameObject) -> str:
    """Print information about a district."""

    district = obj.try_component(District)

    if district is None:
        return ""

    output = [
        "=== District ===",
        "",
        f"Name: {district.name}",
    ]

    if district.locations:
        output.append(f"Locations: (Total {len(district.locations)})")
        for location in district.locations:
            output.append(f"\t- {location.name}")
    else:
        output.append("Locations: None")

    return "\n".join(output)


def _business_section(obj: GameObject) -> str:
    """Print information about a business."""
    business = obj.try_component(Business)

    if business is None:
        return ""

    owner = f"{business.owner.name if business.owner else None}"

    output = [
        "=== Business ===",
        "",
        f"Name: {business.name!r}",
        f"Age: {obj.get_component(Age).value}",
        f"Status: {business.status.name!r}",
        f"Owner: {owner!r} [{business.owner_role.name!r}]",
        f"District: {obj.get_component(CurrentDistrict).district.name!r}",
    ]

    open_positions = business.get_open_positions()
    if open_positions:
        output.append(f"Open Positions: {', '.join(sorted(open_positions))}")
    else:
        output.append("Open Positions: None")

    if business.employees:
        output.append(f"Current Employees: (Total {len(business.employees)})\n")
        employee_table = tabulate.tabulate(
            [
                (employee.name, role.name)
                for employee, role in business.employees.items()
            ],
            headers=("Name", "Role"),
        )
        output.append(employee_table)
    else:
        output.append("Employees: None")

    return "\n".join(output)


def _character_section(obj: GameObject) -> str:
    """Print information about a character."""
    character = obj.try_component(Character)

    if character is None:
        return ""

    residence = "N/A"
    if resident_of := obj.try_component(ResidentOf):
        residence = f"{resident_of.settlement.name!r}"

    age = obj.get_component(Age).value

    output = [
        "=== Character ===",
        "",
        f"Name: {character.full_name!r}",
        f"Age: {int(age)} ({character.life_stage.name})",
        f"Sex: {character.sex.name}",
        f"Species: {obj.get_component(Species).species.name!r}",
        f"Resident of: {residence}",
    ]

    return "\n".join(output)


def _relationship_section(obj: GameObject) -> str:
    """Print information about a relationship."""

    relationship = obj.try_component(Relationship)

    if relationship is None:
        return ""

    output = "=== Relationship ===\n"
    output += "\n"
    output += f"Owner: {relationship.owner.name}\n"
    output += f"Target: {relationship.target.name}\n"

    return output


def _household_section(obj: GameObject) -> str:
    """Print information about a household."""
    household = obj.try_component(Household)

    if household is None:
        return ""

    output: list[str] = [
        "=== Household ===",
        "",
        f"Head of Household: {household.head.name if household.head else 'N/A'}",
    ]

    if household.members:
        output.append(f"Members: (Total {len(household.members)})")
        for member in household.members:
            output.append(f"\t- {member.name}")
    else:
        output.append("Members: N/A")

    return "\n".join(output)


def _member_of_household_section(obj: GameObject) -> str:
    """Print information about a member of household component."""
    member_of_household = obj.try_component(MemberOfHousehold)

    if member_of_household is None:
        return ""

    household = member_of_household.household.get_component(Household)

    output: list[str] = [
        "=== Member of Household ===",
        "",
        f"Name: {household.gameobject.name}",
        f"Head of Household: {household.head.name if household.head else 'N/A'}",
    ]

    if household.members:
        output.append(f"Members: (Total {len(household.members)})")
        for member in household.members:
            output.append(f"\t- {member.name}")
    else:
        output.append("Members: N/A")

    return "\n".join(output)


def _pregnancy_section(obj: GameObject) -> str:
    """Print information about a pregnancy component."""

    pregnancy = obj.try_component(Pregnant)

    if pregnancy is None:
        return ""

    output = [
        "=== Pregnant ===",
        "",
        f"Partner: {pregnancy.partner.name}",
        f"Due Date: {pregnancy.due_date}",
    ]

    return "\n".join(output)


def _employment_section(obj: GameObject) -> str:
    """Print information about a household."""
    occupation = obj.try_component(Occupation)

    if occupation := obj.try_component(Occupation):
        output: list[str] = [
            "=== Employment ===",
            "",
            f"Role ID: {occupation.job_role.definition_id}",
            f"Role: {occupation.job_role.name}",
            f"Description: {occupation.job_role.description}",
            f"Business: {occupation.business.name}",
            f"Start Date: {occupation.start_date}",
        ]

        return "\n".join(output)
    elif unemployment := obj.try_component(Unemployed):
        output = [
            "=== Employment ===",
            "",
            f"Unemployed Since: {unemployment.timestamp}",
        ]

        return "\n".join(output)

    return ""


def _get_frequented_by_table(obj: GameObject) -> str:
    """Generate a string table for a FrequentedBy component."""
    frequented_by = obj.try_component(Location)

    if frequented_by is None:
        return ""

    output = "=== Frequented By ===\n\n"

    output += tabulate.tabulate(
        [
            (entry.uid, entry.get_component(Character).full_name)
            for entry in frequented_by
        ],
        headers=("UID", "Name"),
    )

    return output


def _get_traits_table(obj: GameObject) -> str:
    """Generate a string table for a Traits component."""
    if not obj.has_component(Traits):
        return ""

    traits = obj.get_component(Traits)

    output = "=== Traits ===\n\n"

    output += tabulate.tabulate(
        [
            (
                entry.trait.definition_id,
                entry.trait.name,
                (entry.duration if entry.has_duration else "N/A"),
                entry.timestamp.to_iso_str(),
                entry.description,
            )
            for entry in traits.traits.values()
        ],
        headers=("ID", "Name", "Duration", "Timestamp", "Description"),
    )

    return output


def _get_personal_history_table(obj: GameObject) -> str:
    """Generate a string table for a PersonalEventHistory component."""
    history = obj.try_component(PersonalEventHistory)

    if history is None:
        return ""

    event_data: list[tuple[str, str]] = [
        (str(event.timestamp), str(event)) for event in history.history
    ]

    output = "=== Event History ===\n\n"

    output += tabulate.tabulate(
        event_data,
        headers=("Timestamp", "Description"),
    )

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

    output = "=== Relationships ===\n\n"

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

    output = "=== Stats ===\n\n"

    output += tabulate.tabulate(
        stats_table_data, headers=("Stat", "Value"), numalign="left"
    )

    return output


def _get_skills_table(obj: GameObject) -> str:
    skill_data = obj.try_component(Skills)

    if skill_data is None:
        return ""

    output = "=== Skills ===\n\n"

    output += tabulate.tabulate(
        [
            (
                skill_id,
                skill.skill.name,
                f"{int(skill.stat.value)}/{int(SKILL_MAX_VALUE)}",
                skill.skill.description,
            )
            for skill_id, skill in skill_data.skills.items()
        ],
        headers=("ID", "Name", "Level", "Description"),
    )

    return output


def _get_frequented_locations_table(obj: GameObject) -> str:
    frequented_locations = obj.try_component(FrequentedLocations)

    if frequented_locations is None:
        return ""

    output = "=== Frequented Locations ===\n\n"

    output += tabulate.tabulate(
        [(entry.uid, entry.name) for entry in frequented_locations],
        headers=("UID", "Name"),
    )

    return output


def _get_beliefs_table(obj: GameObject) -> str:
    """Generate section for GameObject beliefs"""

    beliefs = obj.try_component(HeldBeliefs)
    library = obj.world.resources.get_resource(BeliefLibrary)

    if beliefs is None:
        return ""

    output: list[str] = [
        "=== Beliefs ===",
        "",
    ]

    table = tabulate.tabulate(
        [(entry, library.get_belief(entry).description) for entry in beliefs.get_all()],
        headers=("ID", "Description"),
    )

    output.append(table)

    return "\n".join(output)


def _get_applied_beliefs_table(obj: GameObject) -> str:
    """Generate section for GameObject beliefs"""

    applied_beliefs = obj.try_component(AppliedBeliefs)
    library = obj.world.resources.get_resource(BeliefLibrary)

    if applied_beliefs is None:
        return ""

    output: list[str] = [
        "=== Applied Beliefs ===",
        "",
    ]

    table = tabulate.tabulate(
        [
            (entry, library.get_belief(entry).description)
            for entry in applied_beliefs.get_all()
        ],
        headers=("ID", "Description"),
    )

    output.append(table)

    return "\n".join(output)


def _get_location_preferences_table(obj: GameObject) -> str:
    """Generate section for GameObject beliefs"""

    preferences = obj.try_component(LocationPreferences)
    library = obj.world.resources.get_resource(LocationPreferenceLibrary)

    if preferences is None:
        return ""

    output: list[str] = [
        "=== Location Preferences ===",
        "",
    ]

    table = tabulate.tabulate(
        [(entry, library.get_rule(entry).description) for entry in preferences.rules],
        headers=("ID", "Description"),
    )

    output.append(table)

    return "\n".join(output)


_obj_inspector_sections: list[tuple[str, Callable[[GameObject], str]]] = [
    ("title", _title_section),
    ("settlement", _settlement_section),
    ("district", _district_section),
    ("relationship", _relationship_section),
    ("business", _business_section),
    ("character", _character_section),
    ("household", _household_section),
    ("stats", _get_stats_table),
    ("traits", _get_traits_table),
    ("skills", _get_skills_table),
    ("beliefs", _get_beliefs_table),
    ("location_preferences", _get_location_preferences_table),
    ("applied_beliefs", _get_applied_beliefs_table),
    ("member_of_household", _member_of_household_section),
    ("occupation", _employment_section),
    ("pregnancy", _pregnancy_section),
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


def list_species(sim: Simulation) -> None:
    """List all available species."""

    library = sim.world.resources.get_resource(SpeciesLibrary)

    species = [
        (species.definition_id, species.name, species.description)
        for species in library.instances.values()
    ]

    table = tabulate.tabulate(species, headers=["ID", "Name", "Description"])

    output = "=== Species ===\n"
    output += table
    output += "\n"

    print(output)


def list_beliefs(sim: Simulation) -> None:
    """List all available beliefs."""

    library = sim.world.resources.get_resource(BeliefLibrary)

    rows = [(entry.belief_id, entry.description) for entry in library.beliefs.values()]

    table = tabulate.tabulate(rows, headers=["ID", "Description"])

    output = "=== Beliefs ===\n"
    output += table
    output += "\n"

    print(output)


def list_location_preferences(sim: Simulation) -> None:
    """List all available location preferences."""

    library = sim.world.resources.get_resource(LocationPreferenceLibrary)

    rows = [(entry.rule_id, entry.description) for entry in library.rules.values()]

    table = tabulate.tabulate(rows, headers=["ID", "Description"])

    output = "=== Location Preferences ===\n"
    output += table
    output += "\n"

    print(output)


def inspect_trait(sim: Simulation, trait_id: str) -> None:
    """Display information about a trait."""

    trait = sim.world.resources.get_resource(TraitLibrary).get_trait(trait_id)

    lines: list[str] = [
        "TRAIT",
        "=====",
        f"ID: {trait.definition_id!r}",
        f"Name: {trait.name!r}",
        f"Description: {trait.description!r}",
        f"Trait Type: {trait.trait_type.name!r}",
    ]

    # Add effects
    if trait.effects:
        lines.append("Effects:")
        for effect in trait.effects:
            lines.append(f"\t- {effect.description}")
    else:
        lines.append("Effects: N/A")

    # Add incoming/outgoing relationship effects and inheritance
    if trait.trait_type == TraitType.AGENT:
        if trait.incoming_relationship_effects:
            lines.append("Incoming Relationship Effects:")
            for effect in trait.incoming_relationship_effects:
                lines.append(f"\t- {effect.description}")
        else:
            lines.append("Incoming Relationship Effects: N/A")

        if trait.outgoing_relationship_effects:
            lines.append("Outgoing Relationship Effects:")
            for effect in trait.outgoing_relationship_effects:
                lines.append(f"\t- {effect.description}")
        else:
            lines.append("Outgoing Relationship Effects: N/A")

        lines.append(f"Spawn Frequency: {trait.spawn_frequency}")

        lines.append(f"Is Inheritable: {trait.is_inheritable}")

        if trait.is_inheritable:
            lines.append("Inheritance chances if parents have trait:")
            lines.append(f"\t- one parent: {trait.inheritance_chance_single}")
            lines.append(f"\t- both parents: {trait.inheritance_chance_both}")

    # Add information about owner and target effects
    else:
        if trait.owner_effects:
            lines.append("relationship owner effects:")
            for effect in trait.owner_effects:
                lines.append(f"- {effect.description}")
        else:
            lines.append("relationship owner effects: N/A")

        if trait.target_effects:
            lines.append("relationship target effects:")
            for effect in trait.target_effects:
                lines.append(f"- {effect.description}")
        else:
            lines.append("relationship target effects: N/A")

    print("\n".join(lines))


def inspect_skill(sim: Simulation, skill_id: str) -> None:
    """Display information about a skill."""

    skill = sim.world.resources.get_resource(SkillLibrary).get_skill(skill_id)

    if skill.tags:
        tags = ", ".join(sorted(list(skill.tags)))
    else:
        tags = "N/A"

    lines: list[str] = [
        "Skill",
        "=====",
        f"ID: {skill.definition_id!r}",
        f"Name: {skill.name!r}",
        f"Description: {skill.description!r}",
        f"Tags: {tags}",
    ]

    print("\n".join(lines))


def inspect_job_role(sim: Simulation, role_id: str) -> None:
    """Display information about a job role."""

    role = sim.world.resources.get_resource(JobRoleLibrary).get_role(role_id)

    lines: list[str] = [
        "Job Role",
        "========",
        f"ID: {role.definition_id!r}",
        f"Name: {role.name!r}",
        f"Description: {role.description!r}",
        f"Job Level: {role.job_level}",
    ]

    # Add requirements
    if role.requirements:
        lines.append("Requirements:")
        for requirement in role.requirements:
            lines.append(f"\t- {requirement.description}")
    else:
        lines.append("Requirements: N/A")

    # Add Effects
    if role.effects:
        lines.append("Effects:")
        for effect in role.effects:
            lines.append(f"\t- {effect.description}")
    else:
        lines.append("Effects: N/A")

    # Add Recurring Effects
    if role.recurring_effects:
        lines.append("Recurring Effects (Monthly):")
        for effect in role.recurring_effects:
            lines.append(f"\t- {effect.description}")
    else:
        lines.append("Recurring Effects (Monthly): N/A")

    print("\n".join(lines))


def inspect_species(sim: Simulation, species_id: str) -> None:
    """Display information about a species."""

    species = sim.world.resources.get_resource(SpeciesLibrary).get_species(species_id)

    if species.traits:
        traits = ", ".join(species.traits)
    else:
        traits = "N/A"

    lines: list[str] = [
        "Species",
        "========",
        f"ID: {species.definition_id!r}",
        f"Name: {species.name!r}",
        f"Description: {species.description!r}",
        f"Adolescent Age: {species.adolescent_age}",
        f"YoungAdult Age: {species.young_adult_age}",
        f"Adult Age: {species.adult_age}",
        f"Senior Age: {species.senior_age}",
        f"Lifespan: {species.lifespan[0]} - {species.lifespan[1]}",
        f"Can Physically Age: {species.can_physically_age}",
        f"Traits: {traits}",
    ]

    print("\n".join(lines))


def inspect_belief(sim: Simulation, belief_id: str) -> None:
    """Display information about a belief."""

    belief = sim.world.resources.get_resource(BeliefLibrary).get_belief(belief_id)

    lines: list[str] = [
        "Belief",
        "======",
        f"ID: {belief.belief_id!r}",
        f"Description: {belief.description!r}",
        f"Is Global: {belief.is_global}",
    ]

    # Add requirements
    if belief.preconditions:
        lines.append("Preconditions:")
        for precondition in belief.preconditions:
            lines.append(f"\t- {precondition.description}")
    else:
        lines.append("Preconditions: N/A")

    # Add Effects
    if belief.effects:
        lines.append("Effects:")
        for effect in belief.effects:
            lines.append(f"\t- {effect.description}")
    else:
        lines.append("Effects: N/A")

    print("\n".join(lines))


def inspect_location_preference(sim: Simulation, rule_id: str) -> None:
    """Display information about a location preference."""

    rule = sim.world.resources.get_resource(LocationPreferenceLibrary).get_rule(rule_id)

    lines: list[str] = [
        "Location Preference",
        "===================",
        f"ID: {rule.rule_id!r}",
        f"Description: {rule.description!r}",
    ]

    # Add requirements
    if rule.preconditions:
        lines.append("Preconditions:")
        for precondition in rule.preconditions:
            lines.append(f"\t- {precondition.description}")
    else:
        lines.append("Preconditions: N/A")

    # Add consideration
    lines.append(f"Score Consideration: {rule.probability}")

    print("\n".join(lines))
