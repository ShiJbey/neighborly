"""Business Agent Actions."""


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


def lay_off_employee(self) -> None:
    business = self.roles["business"]
    employee = self.roles["subject"]

    current_date = self.world.resources.get_resource(SimDate)

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

    employee.add_component(Unemployed(timestamp=current_date))
    employee.remove_component(Occupation)


def close_for_business(self) -> None:
    business = self.roles["business"]
    business_comp = business.get_component(Business)

    # Update the business as no longer active
    business.remove_component(OpenForBusiness)
    business.add_component(ClosedForBusiness())

    # Remove all the employees
    for employee, role in [*business_comp.employees.items()]:
        LaidOffFromJob(
            subject=employee,
            business=business,
            job_role=role.gameobject,
        ).dispatch()

    # Remove the owner if applicable
    if business_comp.owner is not None:
        LeaveJob(
            business=business,
            subject=business_comp.owner,
            job_role=business_comp.owner_role.gameobject,
            reason="business closed",
        ).dispatch()

    # Decrement the number of this type
    business_comp.district.get_component(BusinessSpawnTable).decrement_count(
        business.metadata["definition_id"]
    )
    business_comp.district.get_component(District).remove_business(business)

    # Remove any other characters that frequent the location
    remove_all_frequenting_characters(business)

    # Un-mark the business as active so it doesn't appear in queries
    business.deactivate()


def start_job(self) -> None:
    character = self.roles["subject"]
    business = self.roles["business"]
    job_role = self.roles["job_role"]

    business_comp = business.get_component(Business)
    current_date = self.world.resources.get_resource(SimDate)

    character.add_component(
        Occupation(
            business=business,
            start_date=current_date,
            job_role=job_role.get_component(JobRole),
        )
    )

    add_frequented_location(character, business)

    if character.has_component(Unemployed):
        character.remove_component(Unemployed)

    # Update boss/employee relationships if needed
    if business_comp.owner is not None:
        add_trait(get_relationship(character, business_comp.owner), "boss")
        add_trait(get_relationship(business_comp.owner, character), "employee")

    # Update employee/employee relationships
    for employee, _ in business_comp.employees.items():
        add_trait(get_relationship(character, employee), "coworker")
        add_trait(get_relationship(employee, character), "coworker")

    business_comp.add_employee(character, job_role.get_component(JobRole))


def open_business(self) -> None:
    character = self.roles["subject"]
    business = self.roles["business"]
    business_comp = business.get_component(Business)
    job_role = business_comp.owner_role
    current_date = self.world.resources.get_resource(SimDate)

    character.add_component(
        Occupation(business=business, start_date=current_date, job_role=job_role)
    )

    add_frequented_location(character, business)

    business_comp.set_owner(character)

    business.remove_component(PendingOpening)
    business.add_component(OpenForBusiness())
    business.add_component(OpenToPublic())

    if character.has_component(Unemployed):
        character.remove_component(Unemployed)


def fire_employee(self) -> None:
    subject = self.roles["subject"]
    business = self.roles["business"]
    job_role = self.roles["job_role"]

    # Events can dispatch other events
    LeaveJob(
        subject=subject, business=business, job_role=job_role, reason="fired"
    ).dispatch()

    business_data = business.get_component(Business)

    owner = business_data.owner
    if owner is not None:
        get_stat(get_relationship(subject, owner), "reputation").base_value -= 20
        get_stat(get_relationship(owner, subject), "reputation").base_value -= 10
        get_stat(get_relationship(subject, owner), "romance").base_value -= 30


def promote_employee(self) -> None:
    character = self.roles["subject"]
    business = self.roles["business"]
    new_role = self.roles["new_role"]

    business_data = business.get_component(Business)

    # Remove the old occupation
    character.remove_component(Occupation)

    business_data.remove_employee(character)

    # Add the new occupation
    character.add_component(
        Occupation(
            business=business,
            start_date=self.world.resources.get_resource(SimDate),
            job_role=new_role.get_component(JobRole),
        )
    )

    business_data.add_employee(character, new_role.get_component(JobRole))


def promote_employee_to_owner(self) -> None:
    subject = self.roles["subject"]
    business = self.roles["business"]

    if occupation := self.roles["subject"].try_component(Occupation):
        # The new owner needs to leave their current job
        LeaveJob(
            subject=subject,
            business=business,
            job_role=occupation.job_role.gameobject,
            reason="Promoted to business owner",
        ).dispatch()

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
