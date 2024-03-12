"""Helper functions for character operations.

"""

from __future__ import annotations

from neighborly.ecs import GameObject, World
from neighborly.factories.character import CharacterFactory, CharacterGenerationOptions
from neighborly.libraries import CharacterLibrary


def create_character(world: World, options: CharacterGenerationOptions) -> GameObject:
    """Create a new character object.

    Parameters
    ----------
    world
        The world instance to spawn the character into.
    options
        Various creation settings.

    Returns
    -------
    GameObject
        The new character object.
    """

    character_def = world.resources.get_resource(CharacterLibrary).get_definition(
        options.definition_id
    )

    character = world.resources.get_resource(CharacterFactory).instantiate(
        world, character_def, options
    )

    return character


def register_character_def(world: World, definition: CharacterDef) -> None:
    """Add a new character definition for the CharacterLibrary.

    Parameters
    ----------
    world
        The world instance containing the character library.
    definition
        The definition to add.
    """
    world.resources.get_resource(CharacterLibrary).add_definition(definition)


def die(character: GameObject) -> None:
    """Have the character dies"""
    character = self.roles["subject"]
    remove_all_frequented_locations(character)
    character.deactivate()
    add_trait(character, "deceased")

    deactivate_relationships(character)

    # Remove the character from their residence
    if resident_data := character.try_component(Resident):
        residence = resident_data.residence
        ChangeResidenceEvent(subject=character, new_residence=None).dispatch()

        # If there are no-more residents that are owner's remove everyone from
        # the residence and have them depart the simulation.
        residence_data = residence.get_component(ResidentialUnit)
        if len(list(residence_data.owners)) == 0:
            residents = list(residence_data.residents)
            for resident in residents:
                DepartSettlement(resident, "death in family")

    # Adjust relationships
    for rel in get_relationships_with_traits(character, "dating"):
        target = rel.get_component(Relationship).target

        remove_trait(rel, "dating")
        remove_trait(get_relationship(target, character), "dating")

        add_trait(rel, "ex_partner")
        add_trait(get_relationship(target, character), "ex_partner")

    for rel in get_relationships_with_traits(character, "spouse"):
        target = rel.get_component(Relationship).target

        remove_trait(rel, "spouse")
        remove_trait(get_relationship(target, character), "spouse")

        add_trait(rel, "ex_spouse")
        add_trait(get_relationship(target, character), "ex_spouse")

        add_trait(rel, "widow")

    # Remove the character from their occupation
    if occupation := character.try_component(Occupation):
        LeaveJob(
            subject=character,
            business=occupation.business,
            job_role=occupation.job_role.gameobject,
            reason="died",
        ).dispatch()


def depart_settlement(self) -> None:
    character = self.roles["subject"]

    remove_all_frequented_locations(character)
    add_trait(character, "departed")
    character.deactivate()

    deactivate_relationships(character)

    # Have the character leave their job
    if occupation := character.try_component(Occupation):
        if occupation.business.get_component(Business).owner == character:
            BusinessClosedEvent(
                subject=character, business=occupation.business
            ).dispatch()
        else:
            LeaveJob(
                subject=character,
                business=occupation.business,
                job_role=occupation.job_role.gameobject,
                reason="departed settlement",
            ).dispatch()

    # Have the character leave their residence
    if resident_data := character.try_component(Resident):
        residence_data = resident_data.residence.get_component(ResidentialUnit)
        ChangeResidenceEvent(subject=character, new_residence=None).dispatch()

        # Get people that this character lives with and have them depart with their
        # spouse(s) and children. This function may need to be refactored in the future
        # to perform BFS on the relationship tree when moving out extended families
        # living within the same residence
        for resident in list(residence_data.residents):
            if resident == character:
                continue

            rel_to_resident = get_relationship(character, resident)

            if has_trait(rel_to_resident, "spouse") and not has_trait(
                resident, "departed"
            ):
                DepartSettlement(resident).dispatch()

            elif has_trait(rel_to_resident, "child") and not has_trait(
                resident, "departed"
            ):
                DepartSettlement(resident).dispatch()


def try_to_find_own_place(self) -> None:
    subject = self.roles["subject"]

    vacant_housing = subject.world.get_components((ResidentialUnit, Vacant))

    if vacant_housing:
        _, (residence, _) = vacant_housing[0]
        ChangeResidenceEvent(
            subject, new_residence=residence.gameobject, is_owner=True
        ).dispatch()

    else:
        ChangeResidenceEvent(subject, new_residence=None).dispatch()
        DepartSettlement(subject).dispatch()


def start_business(self) -> None:
    subject_0, subject_1 = self.roles.get_all("subject")

    remove_trait(get_relationship(subject_0, subject_1), "dating")
    remove_trait(get_relationship(subject_1, subject_0), "dating")

    add_trait(get_relationship(subject_0, subject_1), "spouse")
    add_trait(get_relationship(subject_1, subject_0), "spouse")

    # Update residences
    shared_residence = subject_0.get_component(Resident).residence

    ChangeResidenceEvent(
        subject_1, new_residence=shared_residence, is_owner=True
    ).dispatch()

    for rel in get_relationships_with_traits(subject_1, "child", "live_together"):
        target = rel.get_component(Relationship).target
        ChangeResidenceEvent(target, new_residence=shared_residence).dispatch()

    # Update step sibling relationships
    for rel_0 in get_relationships_with_traits(subject_0, "child"):
        if not rel_0.is_active:
            continue

        child_0 = rel_0.get_component(Relationship).target

        for rel_1 in get_relationships_with_traits(subject_1, "child"):
            if not rel_1.is_active:
                continue

            child_1 = rel_1.get_component(Relationship).target

            add_trait(get_relationship(child_0, child_1), "step_sibling")
            add_trait(get_relationship(child_0, child_1), "sibling")
            add_trait(get_relationship(child_1, child_0), "step_sibling")
            add_trait(get_relationship(child_1, child_0), "sibling")

    # Update relationships parent/child relationships
    for rel in get_relationships_with_traits(subject_0, "child"):
        if rel.is_active:
            child = rel.get_component(Relationship).target
            if not has_trait(get_relationship(subject_1, child), "child"):
                add_trait(get_relationship(subject_1, child), "child")
                add_trait(get_relationship(subject_1, child), "step_child")
                add_trait(get_relationship(child, subject_1), "parent")
                add_trait(get_relationship(child, subject_1), "step_parent")

    for rel in get_relationships_with_traits(subject_1, "child"):
        if rel.is_active:
            child = rel.get_component(Relationship).target
            if not has_trait(get_relationship(subject_0, child), "child"):
                add_trait(get_relationship(subject_0, child), "child")
                add_trait(get_relationship(subject_0, child), "step_child")
                add_trait(get_relationship(child, subject_0), "parent")
                add_trait(get_relationship(child, subject_0), "step_parent")


def form_crush(self) -> None:
    subject = self.roles["subject"]
    other = self.roles["other"]

    # remove existing crushes
    for rel in get_relationships_with_traits(subject, "crush"):
        remove_trait(rel, "crush")

    add_trait(get_relationship(subject, other), "crush")


def retire_from_job(self) -> None:
    subject = self.roles["subject"]
    business = self.roles["business"]
    job_role = self.roles["job_role"]

    add_trait(subject, "retired")

    if business.get_component(Business).owner == subject:
        # Try to find a successor
        business_data = business.get_component(Business)

        potential_successions: list[PromotedToBusinessOwner] = []
        succession_scores: list[float] = []

        for employee, _ in business_data.employees.items():
            succession = PromotedToBusinessOwner(
                subject=employee, business=business, former_owner=subject
            )
            succession_score = succession.get_probability()

            if succession_score >= 0.6:
                potential_successions.append(succession)
                succession_scores.append(succession_score)

        if potential_successions:
            rng = subject.world.resources.get_resource(random.Random)
            chosen_succession = rng.choices(
                population=potential_successions, weights=succession_scores, k=1
            )[0]

            LeaveJob(
                subject=subject,
                business=business,
                job_role=job_role,
                reason="retired",
            ).dispatch()
            chosen_succession.dispatch()
            return

        # Could not find suitable successors. Just leave and lay people off.
        LeaveJob(
            subject=subject,
            business=business,
            job_role=job_role,
            reason="retired",
        ).dispatch()
        BusinessClosedEvent(subject, business, "owner retired").dispatch()
        return

    # This is an employee. Keep the business running as usual
    LeaveJob(subject=subject, business=business, job_role=job_role).dispatch()


def become_friends(self) -> None:
    subject = self.roles["subject"]
    other = self.roles["other"]
    add_trait(get_relationship(subject, other), "friend")
    add_trait(get_relationship(other, subject), "friend")
