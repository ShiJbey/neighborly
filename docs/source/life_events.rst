Life Events
===========

``LifeEvents`` are events represent significant happenings in the lives of characters and other
GameObjects. They are propagated through the ECS using the ``.fire_event(event)`` method on the
GameObjects involved. An example of a life event is provided below.

LifeEvents are what we use to track character background histories. They are
meant to be more narratively meaningful than events like ``ComponentRemovedEvent``.
LifeEvents are added to characters' ``EventHistory`` components when they fired
with the `.fire_event()` method.

Each life event has a date timestamp and list of roles. Each role binds a character to a role name.
You can see it below in the ``BirthEvent`` constructor.

.. code-block:: python

    # This is a birth event that signals that a character was born

    class BirthEvent(LifeEvent):
        def __init__(self, date: SimDateTime, character: GameObject) -> None:
            super().__init__(date, [Role("Character", character)])

        @property
        def character(self):
            return self["Character"]


    character = sim.world.spawn_gameobject()

    character.fire_event(
        BirthEvent(sim.world.get_resource(SimDateTime), character)
    )


Random Life Events
------------------

``RandomLifeEvents`` are where life events become interesting. These are random events
that happen to characters involuntarily. They represent things that are outside of
characters' control. For example, unexpected pregnancies, dying of old age, businesses closing,
etc.

RandomLifeEvents are able to instantiate themselves by binding GameObjects to their roles.
The current process for binding has a lot of boilerplate, but it works well enough to
produce interesting series of events.

Each random life event has a probability of happening, calculated with ``.get_probability()``.

Finally, each random life event has an execute function that makes changes to the simulation
when the event runs.

.. code-block:: python

    # Here is an example of a RandomLifeEvent. Currently, they are called ActionableLifeEvents,
    # but the name will likely change in the future

    # The life event has two roles: PregnantOne and Other. There is no standard method for
    # casting GameObjects into roles for the life event. Currently, we use a series of
    # binding functions that filter results to find matching candidates

    class GetPregnantLifeEvent(ActionableLifeEvent):
        """Defines an event where two characters stop dating"""

        def __init__(
            self, date: SimDateTime, pregnant_one: GameObject, other: GameObject
        ) -> None:
            super().__init__(
                date, [Role("PregnantOne", pregnant_one), Role("Other", other)]
            )

        @staticmethod
        def _bind_pregnant_one(
            world: World, candidate: Optional[GameObject] = None
        ) -> Optional[GameObject]:
            if candidate:
                candidates = [candidate]
            else:
                candidates = [
                    world.get_gameobject(result[0])
                    for result in world.get_components((GameCharacter, Active))
                ]

            candidates = [
                c
                for c in candidates
                if c.has_component(CanGetPregnant) and not c.has_component(Pregnant)
            ]

            if candidates:
                return world.get_resource(random.Random).choice(candidates)

            return None

        @staticmethod
        def _bind_other(
            world: World, initiator: GameObject, candidate: Optional[GameObject] = None
        ) -> Optional[GameObject]:
            if candidate:
                if has_relationship(initiator, candidate) and has_relationship(
                    candidate, initiator
                ):
                    candidates = [candidate]
                else:
                    return None
            else:
                candidates = [
                    world.get_gameobject(c)
                    for c in initiator.get_component(RelationshipManager).outgoing
                ]

            matches: List[GameObject] = []

            for character in candidates:
                outgoing_relationship = get_relationship(initiator, character)

                if not character.has_component(Active):
                    continue

                if not (
                    has_status(outgoing_relationship, Dating)
                    or has_status(outgoing_relationship, Married)
                ):
                    continue

                matches.append(character)

            if matches:
                return world.get_resource(random.Random).choice(matches)

            return None

        @classmethod
        def instantiate(
            cls,
            world: World,
            bindings: RoleList,
        ) -> Optional[ActionableLifeEvent]:
            pregnant_one = cls._bind_pregnant_one(world, bindings.get("Initiator"))

            if pregnant_one is None:
                return None

            other = cls._bind_other(world, pregnant_one, bindings.get("Other"))

            if other is None:
                return None

            return cls(world.get_resource(SimDateTime), pregnant_one, other)

        def execute(self):
            current_date = self["PregnantOne"].world.get_resource(SimDateTime)
            due_date = current_date.copy()
            due_date.increment(months=9)

            self["PregnantOne"].fire_event(self)
            self["PregnantOne"].world.get_resource(AllEvents).append(self)

            add_status(
                self["PregnantOne"],
                Pregnant(
                    partner_id=self["Other"].uid,
                    due_date=due_date,
                ),
            )

        def get_probability(self):
            gameobject = self["PregnantOne"]
            num_children = len(get_relationships_with_statuses(gameobject, ParentOf))

            return 1.0 - (num_children / 5.0)


How are random life events triggered?
-------------------------------------

Random life events are triggered by the ``RandomLifeEventSystem``. It samples a repository of
random life events and triggers those probabilistically.

To add a random life event class type to the repo we use the following:

.. code-block:: python

    RandomLifeEvents.add(DieOfOldAge)

Or we use the ``@random_life_event`` decorator.

.. code-block:: python

    @random_life_event()
    class GetPregnantLifeEvent(ActionableLifeEvent):
        ...
