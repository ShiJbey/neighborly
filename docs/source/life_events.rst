.. _life_events:

Life Events
===========

``LifeEvents`` provide the narrative substance to the simulation. The narratives that emerge from the simulation are sequences of life events combined with observations about the state of the world, and who is engaged in the events. As characters go about their business, life events are selected randomly from a pool and execute given that they meet some preconditions. Life events are then recorded in the simulations ``GlobalEventHistory`` for later processing.

One can think of life events as the major things that happen in a characters life or at least any event that the simulation designer thinks is significant enough to be included in a characters personal backstory (managed by their ``PersonalEventHistory`` component).

Life events are an essential part of specifying character behavior. Internally, they are used to handle things like characters changing life stage, departing from the settlement, moving residences, or dying. Later we discuss how to create new ``LifeEvent`` subtypes.

Defining new LifeEvent types
----------------------------

The following is an example of a ``JobPromotion`` in which a character is promoted from a lower-level to a higher position at the business where they work. There are a few things that users should note.

First, we provide a new constructor that manages setting the roles for an event. The base constructor for ``LifeEvent`` takes the simulations world instance and a Sequence of EventRoles as input. ``EventRoles`` are role names for the event associated with GameObject instances.

Second, there are three consideration functions decorated with ``@staticmethod`` and ``@event_consideration``. These functions change the probability of this event being selected from among the bool of other eligible life events. Each consideration takes a life event as input and returns a probability score between 0 and 1. If a zero is returned, the event's probability is zero. If a negative number is returned, the consideration is ignored from the final probability calculation. The final event probability is the average of the ``base_probability`` with the non negative considerations.

Third, the ``execute`` function contains code that should run when we call the ``dispatch()`` method on the event. This is where we update the world state to reflect the character being promoted from their old role to their new role. Events are allowed to dispatch other life events within their ``execute`` methods.

Fourth, all ``LifeEvent`` subtypes need to override to ``instantiate`` class method. This method is used to create new instances of the life event given the subject of whose life the event pertains to. This is code goes that searches the simulation for other GameObjects to cast into the event's roles. If objects are successfully found for all roles, then we return a new instance of the life event. If not, we return None.

If users do not want an event to be directly triggerable by the ``LifeEventSystem``, they should have the instantiate method just return None. The event will still be constructable by directly using the constructor, but users will not be able to dynamic cast the event's roles.

Finally, we override the ``__str__()`` method to return a string description of the event.

.. code-block:: python

    class JobPromotion(LifeEvent):
        """The character is promoted at their job from a lower role to a higher role."""

        base_probability = 0.5 # <-- The probability without considerations

        def __init__(
            self,
            subject: GameObject,
            business: GameObject,
            old_role: GameObject,
            new_role: GameObject,
        ) -> None:
            super().__init__(
                world=subject.world,
                roles=(
                    EventRole("subject", subject, True),
                    EventRole("business", business),
                    EventRole("old_role", old_role),
                    EventRole("new_role", new_role),
                ),
            )

        @staticmethod
        @event_consideration
        def relationship_with_owner(event: LifeEvent) -> float:
            """Considers the subject's reputation with the business' owner."""
            subject = event.roles["subject"]
            business_owner = event.roles["business"].get_component(Business).owner

            if business_owner is not None:
                return get_stat(
                    get_relationship(business_owner, subject),
                    "reputation",
                ).normalized

            return -1

        @staticmethod
        @event_consideration
        def boldness_consideration(event: LifeEvent) -> float:
            """Considers the subject's boldness stat."""
            return get_stat(event.roles["subject"], "boldness").normalized

        @staticmethod
        @event_consideration
        def reliability_consideration(event: LifeEvent) -> float:
            """Considers the subjects reliability stat."""
            return get_stat(event.roles["subject"], "reliability").normalized

        def execute(self) -> None:
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
                    start_date=self.world.resource_manager.get_resource(SimDate),
                    job_role=new_role.get_component(JobRole),
                )
            )

            business_data.add_employee(character, new_role.get_component(JobRole))

        @classmethod
        def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
            rng = subject.world.resource_manager.get_resource(random.Random)

            if subject.has_component(Occupation) is False:
                return None

            occupation = subject.get_component(Occupation)
            current_job_level = occupation.job_role.job_level
            business_data = occupation.business.get_component(Business)
            open_positions = business_data.get_open_positions()

            higher_positions = [
                role
                for role in open_positions
                if (
                    role.job_level > current_job_level
                    and role.check_requirements(subject)
                )
            ]

            if len(higher_positions) == 0:
                return None

            # Get the simulation's random number generator
            rng = subject.world.resource_manager.get_resource(random.Random)

            chosen_role = rng.choice(higher_positions)

            return JobPromotion(
                subject=subject,
                business=business_data.gameobject,
                old_role=occupation.job_role.gameobject,
                new_role=chosen_role.gameobject
            )


        def __str__(self) -> str:
            subject = self.roles["subject"]
            business = self.roles["business"]
            old_role = self.roles["old_role"]
            new_role = self.roles["new_role"]

            return (
                f"{subject.name} was promoted from {old_role.name} to "
                f"{new_role.name} at {business.name}."
            )

Loading events into the simulation
----------------------------------

To load a new LifeEvent subtype into the simulation (to be triggered by the ``LifeEventSystem``), use the ``register_life_event_type(sim, ...)`` helper function provided within the ```neighborly.loaders``` module.

.. code-block:: python

    register_life_event_type(sim, JobPromotion)
