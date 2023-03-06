Content Management
==================

At some point you will want to add your own content to the simulation. We cover the basics of
plugins on the Plugin page. This page talks about the functions used to load content into the
the simulation and where that content is stored.

Adding custom components
------------------------

Components inherit from the `Component` class in `neighborly.core.ecs`. Component information is
managed by the simulation's World instance. If you need to do something special with component
construction, for example, randomizing attribute values, it is recommended that you create a new
factory class for your components.

.. code-block:: python

    class CustomComponent(Component):

        def __init__(self) -> None:
            super().__init__()


    class CustomComponentFactory(IComponentFactory)
        def create(self, **kwargs: Any) -> CustomComponent:
            # Do special stuff
            # ...
            return CustomComponent()



    sim.world.register_component(CustomComponent, factory=CustomComponentFactory())

Adding custom systems
---------------------

Systems can be either subclasses of `ISystem`, `System`, or `SystemGroup`.

.. code-block:: python

    class CustomSystem(System):

        sys-group = "update"

        def run(self, *args: Any, **kwargs: Any) -> None:
            for gid, (game_character, _) in self.world.get_components((GameCharacter, Active)):
                # Do something
                ...

    sim.world.add_system(CustomSystem())

Adding custom resources
------------------------

.. code-block:: python

    class CustomResource:

        def __init__(self) -> None:
            super().__init__()


    sim.world.add_resource(CustomResource)


Decorators
----------
Neighborly supplies users with a set of built-in decorators to assist with adding content. The
aim of the decorators is to make your code easier to read. They are not recommended for use within
plugins, but they are helpful when modeling a simulation within a single python script file. The
decorators are used heavily in the scripts within the `samples` directory.

Here they are:

- **@component(sim)**: registers a new component with the ECS
- **@component_factory(sim, component_type)**: registers the component factory with the ECS
- **@resource(sim, **kwargs)**: constructs an instance of the resource with kwargs and adds it to the simulation
- **@system(sim, **kwargs)**: constructs an instance of the system with kwargs and adds it to the simulation
- **@life_event(sim)** - adds the life event type to the set of events that can randomly occur each timestep.
- **@social_rule(sim, description="...")** - Adds an instance of the rule to the set used in relationship calculations
- **@location_bias_rule(sim, description="...")** - Adds an instance of the rule to the set used to calculate where characters frequent
- **@brain_factory(sim, name="...")** - Adds a factory class that constructs AIBrains for characters
