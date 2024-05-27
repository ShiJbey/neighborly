.. _plugins:

Plugins
=======

Plugins are how Neighborly enables users to inject custom code into the simulation. They may be single Python modules or entire packages. The only requirement is that when importing the plugin, there is a top-level ``load_plugin(sim)`` function available. The ``load_plugin`` function accepts a simulation instance as input and is free to load all types of new content. Including a ``load_plugin`` function is a convention to ensure that users of your plugin will intuitively know how to load it into their simulation.

Take a look at the code below. This is an example of a Neighborly plugin implemented within a single Python file (module).

.. code-block:: python

    """Example Plugin.

    file: example_plugin.py

    """

    from neighborly.simulation import Simulation
    from neighborly.loaders import load_traits, load_skills, load_districts

    def load_plugin(sim: Simulation) -> None:
        """Add plugin data to the simulation."""

        load_traits(sim, "path/to/trait_data")
        load_skills(sim, "path/to/skill_data")
        load_districts(sim, "path/to/district_data")


Users can then load the plugin into their simulation by importing the module and calling the ``load_plugin`` function.

.. code-block:: python

    """Example Simulation Script.

    """

    from neighborly.simulation import Simulation

    import example_plugin


    def main():

        sim = Simulation()

        example_plugin.load_plugin(sim)

        # other_stuff ...

        sim.run_for(years=100)


    if __name__ == "__main__":
        main()


Sharing plugins
---------------

If you want your plugin to be easily shared with other people/projects, please ensure that you follow recommended Python practices for `packaging and distributing code <https://packaging.python.org/en/latest/tutorials/packaging-projects/>`_. You python package can then be installed from from PyPI or using a GitHub URL.
