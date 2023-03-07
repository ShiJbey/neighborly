Entity-Component System
=======================

Neighborly uses a custom entity-component system (ECS) architecture to model the game
world. It allows neighborly to handle the combinatorial complexity of arbitrary 
character and relationship data. An ECS represents entities as a collection of
independent components instead of trying to define a complex inheritance 
hierarchy. ECS architectures have recently gained traction with large game engines as
Unity and Unreal have boasted new data-driven architectures that allow developers to 
scale up to previously unfathomably-large simulations while still maintaining
performance. While we do not get the performance gains, we do enjoy the benefit of
data-driven content authoring and building complexity through systems.

Most of the Neighborly's development time was spent developing necessary
ECS features and determining the best way to model social relationships. Neighborly's
ECS is a combination of features from `Esper <https://github.com/benmoran56/esper>`_, 
`Unity <https://unity.com/>`_, and 
`Bevy <https://bevyengine.org/learn/book/getting-started/ecs/>`_.

General ECS overview
---------------------

ECSs are designed to be an optimization strategy for data-intensive applications
such as games and simulations. The main idea is to separate data from the
processes that operate on that data. Then all similar data structures are stored
together in memory to improve runtime performance by reducing cache misses.

Within an ECS, the world is represented as a collection of entities. Each
entity has a set of components associated with it. Components are collections of
related data that model a particular aspect of the simulation. For example, a
*Position* component might contain two numerical values, *x* and *y*. Systems
are functions that manipulate the data within components to update the simulation.
A common example is *PhysicsSystem* that updates an entities *Position* component
based on the presence of a *Velocity* component.

If you want a more in-depth discussion, please refer to this `FAQ article from
the Flecs ECS library <https://github.com/SanderMertens/ecs-faq#what-is-ecs>`_.

Overview of Neighborly's ECS
----------------------------

Neighborly uses a custom entity-component system built on top of
`Esper <https://github.com/benmoran56/esper>`_ that integrates features from
other ECS and component-based architectures, like 
`Unity's GameObjects <https://docs.unity3d.com/ScriptReference/GameObject.html>`_ or 
global resource objects in
`Bevy's ECS <https://bevyengine.org/learn/book/getting-started/ecs/>`_. Here we explain
each of the core abstractions used in Neighborly's ECS. Hopefully, this should help you
better understand how to define your own components, systems, and resources.

The World
^^^^^^^^^

Every ``Neighborly`` instance has one ``World`` instance that manages all the
GameObjects (entities), Systems, and Resources. The world instance spawns new
GameObjects and keeps track of when components are added and removed from GameObjects.
When defining systems, you will often use the ``get_component(...)`` or 
``get_components()`` functions to query for all GameObjects that have a specified
set of components. The world instance is also reponsible for managing information about
component types such as their associated name and factory instance.

GameObjects (entities)
^^^^^^^^^^^^^^^^^^^^^^

In Neighborly, entities are refered to as "GameObjects" (taken from Unity). GameObjects
are spawned by a ``World`` instance and given a unique identifier. No two GameObjects
should be assigned the same identifier during a single simulaion run. This identifier
is used internally to associate a GameObject with a specific collection of component
instances. 

GameObjects can be organized into parent-child hierarchies. Adding a GameObject as the
child of another GameObject ensures that the child is removed from the simulation when
the parent is removed. We make use of the hierarchy feature by representing relationship
GameObjects as the children of the Character that owns them.

Components
^^^^^^^^^^

Components contain data. They are used to represent various concepts such as names,
ages, position, services, traits, statuses, relationship statuses, and more. Some
components are mainly used to assist in filtering for specific GameObjects when using
``world.get_components()`` function. Sometimes the large number of components can feel
overwhelming, but breaking up state into smaller focused components helps with re-use
and filtering. Components need to be registered with the world instance using either
the ``world.register_component()`` function or the ``@component(sim)`` decorator.

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

Systems
^^^^^^^

Systems are objects that inherit from ``ISystem`` or ``System``. They
override a ``process`` or ``run`` method that gets called every timestep of
the simulation or on a specified interval. Systems can access GameObjects and
their components by querying the world instance for GameObjects containing
particular components.

Systems can only belong to one system group and each system has a priority value, 
specifying when they should run within their group. The higher the priority the sooner 
the system runs. Groups and priorities are specified by overwriting the ``sys-group`` 
and ``priority`` class variables on ISystem subclasses.

System Groups
^^^^^^^^^^^^^

One of the main challenges of workin with an ECS is orchestrating when certain systems
should run. Eventhough systems are generally decoupled, some systems depend on changes 
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

Resources
^^^^^^^^^

Resources are shared object instances that are accessible from the world.
Neighborly uses resource classes to manage configuration data, authored content,
simulation time, random number generation, and more. Many places within the codebase
we use ``world.get_resource(random.Random)`` to access the random number generator 
instance. Resources do not need to inherit from any class. All users need to do is
add an instance to the simulation using ``sim.add_resource(...)`` or 
``world.add_resource(...)``.

Prefabs
^^^^^^^

Prefabs, much like in Unity, are blueprints of how to construct a specific type of 
GameObject. They allow you to specify what components a GameObject should have, what
parameters to pass to the component's factory, prefab metadata, and any child prefabs. 
Prefabs are used to define characters, businesses, residences, and relationships.
They also allow for a type of inheritance, where one prefab can "extend" another, 
adopting it's parents configuration as base, and overwritting and adding data where
necessary.

Getting started
---------------

The easiest way to get started is looking though the sample code and the code for the
included Neighborly plugins. The sample code below is shows how to make a bare-bones
job salary simulation using the ECS. Usually, we let the ``Neighborly`` constructor
create the ``World`` instance instead of doing it directly. However the full Neighborly
instance adds lots of additional content for the simulation and we wanted this example
to be simple.

.. code-block:: python

    import random

    from neighborly.core.ecs import World, Component
    from neighborly.systems import System

    # Creates a new world instance
    world = World()

    # Add a random number generator as a global resource
    world.add_resource(random.Random())


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
            for guid, (money, job) for self.world.get_component(Money, Job):
                # The code below may give errors in some IDEs because
                # the typing isn't the best for Generic return types.
                # There are two solutions to solve this
                # 1) Add '# type: ignore' to the left of the code
                # 2) Import 'cast' from typing and then
                #    money = cast(Money, money)
                #    job = cast(Job, job)
                money.dollars += job.salary
                print(money.dollars)

    # You need to register the component with the world instance
    # to use it with the YAML authoring interface
    world.register_component(Money)

    # Create a new character
    alice = world.spawn_gameobject([
        Actor("Alice"),
        Money(10)
    ])

    # Add the system ti the world
    world.add_system(SalarySystem())

    # Stepping the simulation while Alice has no job will not
    # change her current money
    world.step()

    assert alice.get_component(Money).dollars == 10

    # Adding a Job component makes Alice appear in the SalarySystem's
    # world.get_components(...) query.
    alice.add_component(Job("CEO", 500_000))

    # Now stepping the simulation should allow Alice to get paid
    world.step()

    assert alice.get_component(Money).dollars == 500_010
