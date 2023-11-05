.. _ecs:

Entity-Component System
=======================

Entity-component systems (ECS) is a software architecture pattern that is popular in game development for its performance benefits and ability to represent combinatorially complex objects. It is a way of representing objects in the game world by composing entities out of components that contain data and running systems that operate on and modify components. ECS architectures emphasize representing objects using component composition rather than object-oriented inheritance trees. ECS architectures have a long history in Roguelike game development and have recently gained traction with large game engines like `Unity <https://docs.unity3d.com/Packages/com.unity.entities@1.0/manual/index.html>`_ and `Unreal <https://docs.unrealengine.com/5.0/en-US/overview-of-mass-entity-in-unreal-engine/>`_.

Within an ECS, the world is represented as a collection of entities. Each entity has a set of components associated with it. Components are collections of related data that model a particular aspect of the simulation. For example, a Position component might contain two numerical values, x and y. Systems are functions that manipulate the data within components to update the simulation. A common example is a PhysicsSystem that updates an entity’s Position component based on the presence and values of a Velocity component.

If you want a more in-depth discussion, please refer to this `FAQ article from the Flecs ECS library <https://github.com/SanderMertens/ecs-faq#what-is-ecs>`_.

ECSs are designed to be an optimization strategy for data-intensive applications such as games and simulations. The main idea is to separate data from the processes that operate on that data. Then all similar data structures are stored together in memory to improve runtime performance by reducing cache misses. Neighborly does not get the same performance gains seen with C++ and C#-based ECSs, but it does enjoy the benefit of data-driven content authoring and the iterative layering of complexity through systems.

Neighborly uses a custom entity-component system originally made for Neighborly. It's built on top of `Esper <https://github.com/benmoran56/esper>`_ that integrates features from other ECS and component-based architectures, like `Unity’s GameObjects <https://docs.unity3d.com/ScriptReference/GameObject.html>`_, and global resource objects in `Bevy’s ECS <https://bevyengine.org/learn/book/getting-started/ecs/>`_.

Parts of the ECS
----------------

The World
^^^^^^^^^

The world is the main entry point for the ECS. It manages all the entities (GameObjects), resources, and systems. Every simulation has only one world instance. We use the World instance to query for GameObjects, add/remove global shared resources, spawn GameObjects, and add/remove systems.

Users never have to create new World instances. One is created automatically when we create a new Simulation. It can be accessed using the `sim.world` attribute.

``get_components(...)`` is the main method that users need to know about. It accepts a tuple of component types and returns a list of tuples containing the IDs of GameObjects paired with a tuple of references to components of the given types. So, if we were to call ``sim.world.get_components((Position, Velocity))`` it would return all the GameObjects that have both Position and Velocity components.

GameObjects
^^^^^^^^^^^

Within Neighborly, entities are referred to as “GameObjects” (taken from Unity). GameObjects are spawned by a World instance and given a unique identifier. No two GameObjects should be assigned the same identifier during a single simulation run. Users can add, remove and check for components on GameObject instances. Neighborly uses GameObjects to represent characters, businesses, relationships, and residential buildings.

Components
^^^^^^^^^^

Components contain data. They are used to represent various concepts such as names, ages, position, services, traits, statuses, relationship statuses, and more.

Resources
^^^^^^^^^

Resources are shared object instances. Neighborly stores content definitions within specialized library classes that are exposed as shared resources.

Systems and SystemGroups
^^^^^^^^^^^^^^^^^^^^^^^^

Perform operations every time step and can be grouped inside System groups to help orchestrate what order they run.

By default Neighborly has the following system/system group ordering:

- `InitializationSystems` (runs only once on first timestep)
- `EarlyUpdateSystems`
- `DataCollectionSystems`
- `UpdateSystems`
- `LateUpdateSystems`
