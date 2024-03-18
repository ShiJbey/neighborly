"""Business Agent Actions."""

from neighborly.components.business import Business, BusinessStatus, JobRole, Occupation
from neighborly.components.settlement import District
from neighborly.components.spawn_table import BusinessSpawnTable
from neighborly.datetime import SimDate
from neighborly.ecs import GameObject
from neighborly.helpers.location import (
    add_frequented_location,
    remove_all_frequenting_characters,
    remove_frequented_location,
)
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import add_trait, get_trait, has_trait, remove_trait


def leave_job(subject: GameObject) -> None:
    world = subject.world
    occupation = subject.get_component(Occupation)
    business = occupation.business.get_component(Business)

    current_date = world.resources.get_resource(SimDate)

    remove_frequented_location(subject, business.gameobject)

    if subject == business.owner:

        # Update relationships boss/employee relationships
        for employee, _ in business.employees.items():
            remove_trait(get_relationship(subject, employee), "employee")
            remove_trait(get_relationship(employee, subject), "boss")

    else:
        business.remove_employee(subject)

        # Update boss/employee relationships if needed
        owner = business.owner
        if owner is not None:
            remove_trait(get_relationship(subject, owner), "boss")
            remove_trait(get_relationship(owner, subject), "employee")

        # Update coworker relationships
        for other_employee, _ in business.employees.items():
            if other_employee == subject:
                continue

            remove_trait(get_relationship(subject, other_employee), "coworker")
            remove_trait(get_relationship(other_employee, subject), "coworker")

    add_trait(subject, "unemployed")
    get_trait(subject, "unemployed").data["timestamp"] = current_date

    subject.remove_component(Occupation)


def lay_off_employee(business: GameObject, employee: GameObject) -> None:
    world = business.world
    current_date = world.resources.get_resource(SimDate)

    business_comp = business.get_component(Business)

    remove_frequented_location(employee, business)

    business_comp.remove_employee(employee)

    # Update boss/employee relationships if needed
    owner = business_comp.owner
    if owner is not None:
        remove_trait(get_relationship(employee, owner), "boss")
        remove_trait(get_relationship(owner, employee), "employee")

    # Update coworker relationships
    for other_employee, _ in business_comp.employees.items():
        if other_employee == employee:
            continue

        remove_trait(get_relationship(employee, other_employee), "coworker")
        remove_trait(get_relationship(other_employee, employee), "coworker")

    add_trait(employee, "unemployed")
    get_trait(employee, "unemployed").data["timestamp"] = current_date.copy()
    employee.remove_component(Occupation)


def close_for_business(business: GameObject) -> None:

    business_comp = business.get_component(Business)

    business_comp.status = BusinessStatus.CLOSED

    # Remove all the employees
    for employee, role in [*business_comp.employees.items()]:
        lay_off_employee(
            subject=employee,
            business=business,
            job_role=role.gameobject,
        )

    # Remove the owner if applicable
    if business_comp.owner is not None:
        leave_job(
            business=business,
            subject=business_comp.owner,
            job_role=business_comp.owner_role.gameobject,
            reason="business closed",
        )

    # Decrement the number of this type
    business_comp.district.get_component(BusinessSpawnTable).decrement_count(
        business.metadata["definition_id"]
    )
    business_comp.district.get_component(District).remove_business(business)

    # Remove any other characters that frequent the location
    remove_all_frequenting_characters(business)

    # Un-mark the business as active so it doesn't appear in queries
    business.deactivate()


def start_job(
    character: GameObject, business: GameObject, job_role: GameObject
) -> None:
    world = character.world

    business_comp = business.get_component(Business)
    current_date = world.resources.get_resource(SimDate)

    character.add_component(
        Occupation(
            business=business,
            start_date=current_date,
            job_role=job_role.get_component(JobRole),
        )
    )

    add_frequented_location(character, business)

    if has_trait(character, "unemployed"):
        remove_trait(character, "unemployed")

    # Update boss/employee relationships if needed
    if business_comp.owner is not None:
        add_trait(get_relationship(character, business_comp.owner), "boss")
        add_trait(get_relationship(business_comp.owner, character), "employee")

    # Update employee/employee relationships
    for employee, _ in business_comp.employees.items():
        add_trait(get_relationship(character, employee), "coworker")
        add_trait(get_relationship(employee, character), "coworker")

    business_comp.add_employee(character, job_role.get_component(JobRole))


def open_business(character: GameObject, business: GameObject) -> None:
    world = character.world
    business_comp = business.get_component(Business)
    job_role = business_comp.owner_role
    current_date = world.resources.get_resource(SimDate)

    character.add_component(
        Occupation(business=business, start_date=current_date, job_role=job_role)
    )

    add_frequented_location(character, business)

    business_comp.set_owner(character)
    business_comp.status = BusinessStatus.OPEN

    if has_trait(character, "unemployed"):
        remove_trait(character, "unemployed")


def fire_employee(
    business: GameObject, subject: GameObject, job_role: GameObject
) -> None:

    # Events can dispatch other events
    leave_job(subject=subject, business=business, job_role=job_role, reason="fired")

    business_data = business.get_component(Business)

    owner = business_data.owner
    if owner is not None:
        get_stat(get_relationship(subject, owner), "reputation").base_value -= 20
        get_stat(get_relationship(owner, subject), "reputation").base_value -= 10
        get_stat(get_relationship(subject, owner), "romance").base_value -= 30


def promote_employee(
    business: GameObject, character: GameObject, new_role: GameObject
) -> None:
    world = business.world

    business_data = business.get_component(Business)

    # Remove the old occupation
    character.remove_component(Occupation)

    business_data.remove_employee(character)

    # Add the new occupation
    character.add_component(
        Occupation(
            business=business,
            start_date=world.resources.get_resource(SimDate).copy(),
            job_role=new_role.get_component(JobRole),
        )
    )

    business_data.add_employee(character, new_role.get_component(JobRole))


def promote_employee_to_owner(business: GameObject, subject: GameObject) -> None:

    if occupation := subject.try_component(Occupation):
        # The new owner needs to leave their current job
        leave_job(
            subject=subject,
            business=business,
            job_role=occupation.job_role.gameobject,
            reason="Promoted to business owner",
        )

    # Set the subject as the new owner of the business
    business_data = business.get_component(Business)
    current_date = subject.world.resources.get_resource(SimDate)

    subject.add_component(
        Occupation(
            business=business,
            start_date=current_date,
            job_role=business_data.owner_role,
        )
    )

    add_frequented_location(subject, business)

    business_data.set_owner(subject)

    # Update relationships boss/employee relationships
    for employee, _ in business_data.employees.items():
        add_trait(get_relationship(subject, employee), "employee")
        add_trait(get_relationship(employee, subject), "boss")
