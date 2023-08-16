Entity-Component System
=======================

Neighborly uses a custom entity-component system (ECS) architecture to model the game
world. It allows Neighborly to handle the combinatorial complexity of arbitrary
character, relationship, building, and data.

An ECS represents entities as a collection of
independent components instead of trying to define a complex inheritance
hierarchy. ECS architectures have a long history in Roguelike game development, and
have recently gained traction with large game engines like
`Unity <https://docs.unity3d.com/Packages/com.unity.entities@1.0/manual/index.html>`_
and `Unreal <https://docs.unrealengine.com/5.0/en-US/overview-of-mass-entity-in-unreal-engine/>`_.

Within an ECS, the world is represented as a collection of entities. Each
entity has a set of components associated with it. Components are collections of
related data that model a particular aspect of the simulation. For example, a
*Position* component might contain two numerical values, *x* and *y*. Systems
are functions that manipulate the data within components to update the simulation.
A common example is a *PhysicsSystem* that updates an entity's *Position* component
based on the presence and values of a *Velocity* component.

If you want a more in-depth discussion, please refer to this `FAQ article from
the Flecs ECS library <https://github.com/SanderMertens/ecs-faq#what-is-ecs>`_.

ECSs are designed to be an optimization strategy for data-intensive applications
such as games and simulations. The main idea is to separate data from the
processes that operate on that data. Then all similar data structures are stored
together in memory to improve runtime performance by reducing cache misses.
Neighborly does not get the same performance gains seen with C++ and C#-based ECSs, but
it does enjoy the benefit of data-driven content authoring and the iterative layering
of complexity through systems.

Overview of Neighborly's ECS
----------------------------

Most of the Neighborly's development time was spent building the necessary ECS
infrastructure to support easy content authoring and end-user expansion of pre-authored
content. Neighborly uses a custom entity-component system built on top of
`Esper <https://github.com/benmoran56/esper>`_ that integrates features from
other ECS and component-based architectures, like
`Unity's GameObjects <https://docs.unity3d.com/ScriptReference/GameObject.html>`_,
global resource objects in
`Bevy's ECS <https://bevyengine.org/learn/book/getting-started/ecs/>`_, and
`event handling from Caves of Qud <https://www.youtube.com/watch?v=U03XXzcThGU>`_.

Here we explain each of the core abstractions used in Neighborly's ECS. Hopefully,
this should help you better understand how to define your own components, systems,
resources, and events.

The World
^^^^^^^^^

Every ``Neighborly`` instance has one ``World`` instance that manages all the
GameObjects (entities), Systems, and Resources. The world instance spawns new
GameObjects and keeps track of when components are added and removed from GameObjects.
When defining systems, you will often use the ``get_component(...)`` or
``get_components()`` functions to query for all GameObjects that have a specified
set of components. The world instance is also responsible for managing information about
component types such as their associated name and factory instance.


.. code-block:: python

    from neighborly.core.ecs import World
    from neighborly import Neighborly

    # Usually you would not create a lone world instance, but if you just want
    # the bare-bones ECS without starting content, this is how
    world = World()

    # You can now spawn empty game objects
    gameobject_1 = world.spawn_gameobject()

    # If you want all the built-in component factories and such to be available
    # then you should access the World instance inside a Neighborly instance
    sim = Neighborly()

    # You can now spawn empty game objects
    gameobject_2 = sim.world.spawn_gameobject()



GameObjects (entities)
^^^^^^^^^^^^^^^^^^^^^^

In Neighborly, entities are referred to as "GameObjects" (taken from Unity). GameObjects
are spawned by a ``World`` instance and given a unique identifier. No two GameObjects
should be assigned the same identifier during a single simulation run. This identifier
is used internally to associate a GameObject with a specific collection of component
instances.

GameObjects can be organized into parent-child hierarchies. Adding a GameObject as the
child of another GameObject ensures that the child is removed from the simulation when
the parent is removed. We make use of the hierarchy feature by representing relationship
GameObjects as the children of the Character that owns them.

.. code-block:: python

    from neighborly import Neighborly
    from neighborly.components import GameCharacter, Age

    sim = Neighborly()

    # Spawns a new gameobject with the given list of components
    character = sim.world.spawn_gameobject(
        [
            GameCharacter("Jane", "Doe"),
            Age(27)
        ]
    )

    # Prints all the components attached to the character
    print(character.get_components())

    # Components on a GameObject are accessed using the component class type
    # Prints "27"
    print(character.get_component(Age).value)

    # prints "Jane Doe"
    print(character.get_component(GameCharacter).full_name)

    character.remove_component(Age)

    # Raises a ComponentNotFoundError
    print(character.get_component(Age).value)

Components
^^^^^^^^^^

Components contain data. They are used to represent various concepts such as names,
ages, position, services, traits, statuses, relationship statuses, and more. Some
components are mainly used to assist in filtering for specific GameObjects when using
``world.get_components()`` function. Sometimes the large number of components can feel
overwhelming, but breaking up state into smaller focused components helps with re-use
and filtering. Components need to be registered with the world instance using either
the ``world.register_component()`` function or the ``@component(sim)`` decorator.

.. code-block:: python

    # This sample shows users can create new classes of components and apply them
    # to GameObject instances

    from neighborly import Neighborly
    from neighborly.core.ecs import Component
    from neighborly.components import GameCharacter, Age

    class AbilityScores(Component):

        def __init__(
            self,
            strength = 0,
            dexterity = 0,
            constitution = 0,
            wisdom = 0,
            charisma = 0
        ) -> None:
            self.strength: int = strength
            self.dexterity: int = dexterity
            self.constitution: int = constitution
            self.intelligence: int = intelligence
            self.wisdom: int = wisdom
            self.charisma: int = charisma


    sim = Neighborly()

    # Spawns a new gameobject with the given list of components
    # Here we manually specify the values for each
    character = sim.world.spawn_gameobject(
        [
            GameCharacter("Jane", "Doe"),
            Age(27),
            AbilityScores(
                strength=11,
                charisma=16,
                wisdom=10,
                constitution=7,
                dexterity=9
            )
        ]
    )

Component Factories
^^^^^^^^^^^^^^^^^^^

Component factories allow us to construct components using data files. When a component
is registered with the ECS, by default is is associated with a factory instance that
passes keyword arguments directly to the component's constructor. Users can override
this if they need to do something special when constructing a component. Factories give
you access to simulation resources when constructing component instances. For example,
the ``Name`` component uses `Tracery <https://tracery.io/>`_ to generate a name string
based on special syntax. Another example, if you have various stat components like
Strength, Defense, and Speed, you could define a factory for each that accesses the
``random.Random`` resource to randomize starting stats.

.. code-block:: python

    # This sample expands on the first by using a Component Factory to create
    # the AbilityScores components. This sample uses the dice library for
    # score generation: https://pypi.org/project/dice/

    from typing import Any

    import dice

    from neighborly import Neighborly
    from neighborly.core.ecs import Component, IComponentFactory
    from neighborly.components import GameCharacter, Age

    # other code removed for brevity

    class AbilityScoresFactory(IComponentFactory):
        def create(self, world: World, **kwargs: Any) -> AbilityScores:
            # Generates scores by simulating rolling four dice, taking the highest
            # three values, and summing those values
            return AbilityScores(
                strength=dice.roll("4d6^3t"),
                charisma=dice.roll("4d6^3t"),
                wisdom=dice.roll("4d6^3t"),
                constitution=dice.roll("4d6^3t"),
                dexterity=dice.roll("4d6^3t")
            )

    character = sim.world.spawn_gameobject(
        [
            GameCharacter("Jane", "Doe"),
            Age(27),
            AbilityScoresFactory().create(sim.world)
        ]
    )

Systems and SystemGroups
^^^^^^^^^^^^^^^^^^^^^^^^

Systems are objects that inherit from ``ISystem`` or ``System``. They
override a ``process`` or ``run`` method that gets called every timestep of
the simulation or on a specified interval. Systems can access GameObjects and
their components by querying the world instance for GameObjects containing
particular components.

One of the main challenges of working with an ECS is orchestrating when certain systems
should run. Even though systems are generally decoupled, some systems depend on changes
that are triggered by other systems. For example, the each character chooses an action
from a pool of actions suggested by various systems each timestep. If the AI runs before
the other systems, then characters will never have actions to take. Or if event-firing
systems run after the event handling systems, then none of the events will be detected.

One solution to this problem is assigning priorities to systems and running them in
priority-order. However, this requires tracking the priorities of all other systems
to ensure that things run without conflict. This was the solution we used in an earlier
version of Neighborly.

System groups are a subtype of system that group together Systems and other
SystemGroups. All systems within a group run before proceeding to the next system in
the ECS. The hierarchical structure and intentional group naming make it much easier
to determine when a system should run. This library's ECS implementation has one
``root`` system group that all systems are assigned to be default. Users are free to
create new groups and assign systems as they see fit. System groups are defined
the same as systems.

Systems can only belong to one system group and each system has a priority value,
specifying when they should run within their group. The higher the priority the sooner
the system runs. Groups and priorities are specified by overwriting the ``sys-group``
and ``priority`` class variables on ISystem subclasses.

By default Neighborly has the following system/system group ordering:

- InitializationSystemGroup (runs only once on first timestep)
- EarlyUpdateSystemGroup
    - DataCollectionSystemGroup
    - StatusUpdateSystemGroup
        - PregnantStatusSystem
        - UnemployedStatusSystem
    - Goal SuggestionSystemGroup
    - RelationshipUpdateSystemGroup
        - RelationshipUpdateSystem
        - FriendshipStatSystem
        - RomanceStatSystem
    - MeetNewPeopleSystem
    - RandomLifeEventSystem
    - UpdateFrequentedLocationSystem
- UpdateSystemGroup
    - CharacterAgingSystem
    - AIActionSystem
- LateUpdateSystemGroup


Resources
^^^^^^^^^

Resources are shared object instances that are accessible from the world.
Neighborly uses resource classes to manage configuration data, authored content,
simulation time, random number generation, and more. Many places within the codebase
we use ``world.get_resource(random.Random)`` to access the random number generator
instance. Resources do not need to inherit from any class. All users need to do is
add an instance to the simulation using ``sim.world.add_resource(...)``.

.. code-block:: python

    # ... omitted imports and simulation instantiation for brevity

    class SharedResource:
        """Some shared resource"""

        pass

    sim.world.add_resource(SharedResource())

Prefabs
^^^^^^^

Prefabs, like in Unity, are blueprints of how to construct a specific type of
GameObject. They allow you to specify what components a GameObject should have, what
parameters to pass to the component's factory, prefab metadata, and any child prefabs.
Prefabs are used to define characters, businesses, residences, and relationships.
They also allow for a type of inheritance, where one prefab can "extend" another,
adopting it's parents configuration as base, and overwriting and adding data where
necessary.

To use a component in a prefab file, users need to ensure that the component type has
been registered with the simulation's World instance. Also, users should be sure to
register component factories if needed.

Prefabs are specified in YAML files and loaded at runtime. We can then create an
instance of the prefab using the ``GameObjectFactory`` class.

.. code-block:: yaml

    # sample_character_prefab.yaml

    # The name of the prefab should be unique. The :: namespace
    # notation is not required. We use it internally to differentiate
    # built-in content from user-created content
    name: "character::sample"
    # (optional) Marks this prefab as not being able to be instantiated.
    # Attempting to instantiate a template will result in an error
    is_template: false
    # (optional) Prefabs can extend one or more other prefabs. This means that this
    # prefab definition will get all the components from the parent prefabs
    # and can overwrite these components in its definition
    extends: [""]
    # The components section  contains a map of component type names mapped
    # to keyword arguments to be passed to the component's registered factory.
    # If a component appears within one of the prefabs listed int the extends
    # section, it will be replaced with the parameters listed here.
    components:
        GameCharacter:
            first_name: "#character::default::first_name::gender-neutral#"
            last_name: "#character::default::last_name#"
        AgingConfig:
            adolescent_age: 13
            young_adult_age: 18
            adult_age: 30
            senior_age: 65
        Lifespan:
            value: 85
        MarriageConfig:
            spouse_prefabs:
            - "character::default::.*"
            chance_spawn_with_spouse: 0.5
        ReproductionConfig:
            max_children_at_spawn: 3
            child_prefabs:
            - "character::default::.*"
        # Components with empty { } next to their will no have keyword argument passed
        # to their factories
        RelationshipManager: { }
        Virtues: { }
        CanAge: { }
        StatusManager: { }
        FrequentedLocations: { }
        AIBrain: { }
        Goals: { }
        EventHistory: { }
        Age: { }
        Gender:
            gender: NotSpecified
        LifeStage:
            life_stage: Adult
        AbilityScores: { }


Then we can use it in python like this:

.. code-block:: python

    from neighborly.loaders import load_prefabs

    # ... omitted imports and simulation instantiation for brevity

    # Here we register the AbilityScores component from the previous samples
    # and we added it as a component in our prefab definition above
    sim.world.register_component(AbilityScores, factory=AbilityScoresFactory())

    # We have a utility function that loads prefab data from YAML or
    # JSON files located at the given path
    load_prefabs("sample_character_prefab.yaml")



    # The GameObjectFactory class handles instantiating loaded prefabs
    # It takes a World instance and the name of the prefab as parameters
    # The prefab name is the one specified in the YAML
    character = GameObjectFactory.instantiate(sim.world, "character::sample")


Events
------

Users can attach event listener functions to GameObjects. This feature was added to
allow components to communicate with each other, and for user-created content to
tap into built-in and third-party content. By default events are used for component
addition/removal detection. We also use them for signaling things like LifeEvents that
have happened to characters. Currently, event listeners are registered to the GameObject
class. So, all GameObjects have the same listeners. However, listeners are only fired
when their specific event fires. Below is an example. Another example is using
``ComponentAddedEvent`` and ``ComponentRemovedEvent`` to modify things like character
ability scores when certain buffs are added or removed.


.. code-block:: python

    class CustomEvent:

        def __init__(self, data) -> None:
            self.data = data

    def custom_event_listener(gameobject, event):
        # Print the event data to the console
        print(event.data)


    GameObject.on(CustomEvent, custom_event_listener)

    gameobject = sim.world.spawn_gameobject()

    gameobject.fire_event(CustomEvent("This is an event"))

    # Event listeners can also register to be called for any event
    # regardless of type

    def general_event_listener(gameobject, event):
        print(f"An event fired of type {type(event)}")

    gameobject.on_any(general_event_listener)

    gameobject.fire_event(CustomEvent("This is another event"))



Small ECS Sample
----------------

The easiest way to get started is looking though the sample code and the code for the
included Neighborly plugins. The sample code below is shows how to make a
job salary simulation using the ECS.

.. code-block:: python

    import random

    from neighborly import Neighborly
    from neighborly.core.ecs import World, Component
    from neighborly.systems import System

    # Creates a new world instance
    sim = Neighborly()

    class Actor(Component):

        __slots__ = "name"

        def __init__(self, name: str) -> None:
            super().__init__()
            self.name: str = name


    class Money(Component):

        __slots__ = "dollars"

        def __init__(self, dollars: int) -> None:
            super().__init__()
            self.dollars: int = dollars


    class Job(Component):

        __slots__ = "title", "salary"

        def __init__(self, title: str, salary: int) -> None:
            super().__init__()
            self.title: str = title
            self.salary: int = salary


    class SalarySystem(System):
        """Increases a characters money by their salary amount"""

        def run(self, *args: Any, **kwargs: Any) -> None:
            for _, (money, job) for self.world.get_components((Money, Job)):
                money.dollars += job.salary
                print(money.dollars)

    # You need to register the component with the world instance
    # to use it with the YAML authoring interface
    sim.world.register_component(Money)

    # Create a new character
    alice = world.spawn_gameobject([
        Actor("Alice"),
        Money(10)
    ])

    # Add the system ti the world
    sim.world.add_system(SalarySystem())

    # Stepping the simulation while Alice has no job will not
    # change her current money
    sim.step()

    assert alice.get_component(Money).dollars == 10

    # Adding a Job component makes Alice appear in the SalarySystem's
    # world.get_components(...) query.
    alice.add_component(Job("CEO", 500_000))

    # Now stepping the simulation should allow Alice to get paid
    sim.step()

    assert alice.get_component(Money).dollars == 500_010
