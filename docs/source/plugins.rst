Plugins
=======

Plugins are at the heart of Neighborly's flexibility. The allow users to modularize and package
their custom simulation content (prefabs, components, and systems). At their base, Neighborly
plugins are just Python modules that are dynamically loaded at runtime.

Neighborly comes prepackaged with a set of plugins that serve as examples and default content for
users to build from. You can find all of these in the `plugins` directory inside Neighborly.

What goes inside a plugin?
--------------------------

- Component definitions
- System definitions
- Resource definitions
- Location bias rules
- Social rules
- Character prefabs
- Business prefabs
- Residence prefabs
- Status definitions
- Trait definitions
- Relationship status definitions
- Relationship facet definitions
- Any thing you can represent as components, systems, and resources!

How are plugins imported?
-------------------------

Plugins are imported at simulation construction. They are specified in the `plugins` field of the
configuration. There are two ways to specify plugins. The first is passing only the name of the
module to import. This works for modules/packages that are installed using pip or present in the
Pythons current import path.

For example, since all built-in Neighborly plugins are installed with the base installation,
you can import them using only the module name.

.. code-block:: python

    NeighborlyConfig(
        plugins=[
            "neighborly.plugins.weather",
            # other plugins ...
        ]
    )


If this is not the case, then you will need to use the second option that specifies the file path
where the plugin is located.

.. code-block:: python

    NeighborlyConfig(
        plugins=[
            {
                "name": "<plugin_name>",
                "path": "./path/to/plugin"
            }
            # other plugins ...
        ]
    )

Optionally, you can also pass key-value pair arguments to  a plugin's setup function if it supports
it. This allows users to modify plugin behavior at import-time. These options should be documented
by the plugin's author(s).

.. code-block:: python

    NeighborlyConfig(
        plugins=[
            {
                "name": "<plugin_name>",
                "path": "./path/to/plugin"
                "options": {
                    "enable_parameter": True
                    # other parameters...
                }
            }
            # other plugins ...
        ]
    )

Creating custom plugins
-----------------------

A plugin can be as simple as a single file or as large as an entire Python package. It is
recommended that you define plugins as packages so that any data files are always packaged with
the Python code. If you would like to distribute your package so that other's can use it, we
recommended following `pythons instructions for packaging and distributing code <https://packaging.python.org/en/latest/tutorials/packaging-projects/>`_

When Neighborly imports your package it looks for two things:

1. A **plugin_info** dict with the plugin's name, unique identifier, plugin version, and version
   of Neighborly required to run
2. A **setup(sim, **kwargs)** function that loads content from the plugin into the simulation

The plugin info and setup function need to be globally visible when importing the plugin. So, they
should be present in the plugin file or top-level `__init__.py` if the plugin is a python package.

Please refer to the built-in Neighborly plugins as an example.


.. Creating your first plugin
.. --------------------------

.. Step 0: Setup
.. ^^^^^^^^^^^^^

.. Create a new directory called ``

.. Step 1: Create a package
.. ^^^^^^^^^^^^^^^^^^^^^^^^

.. Start by creating a folder with the name of your package and then create an `__init__.py` file
.. inside that folder. Python looks for `__init__.py` when attempting to import a folder as Python
.. package.
