Commandline Tool
================

Neighborly includes a commandline tool for generating simulation data. The commandline tool accepts
a configuration file, runs a simulation according to that configuration, and outputs the final
simulation state to a JSON file. Users can start the CLI by running ``neighborly`` or
``python -m neighborly`` in their command line. The CLI runs a *Talk of the Town* clone by default.

Users can customize the CLI's behavior by specifying command-line arguments or
using a configuration file. To view the complete list of command-line arguments,
please use ``neighborly --help`` or ``python -m neighborly --help``.

Configuration files
-------------------

Neighborly accepts YAML and JSON as configuration files. By default, the commandline tool will look
for any of the following files to be present in the current working directory.

These are listed in order of precedence:

- neighborly.config.yaml
- neighborly.config.yml
- neighborly.config.json

If you have do not name your configuration file as one of the names listed above, then you can tell
Neighborly to use a different configuration file by using the ``-c`` or ``--config`` flag followed by
the path to the configuration file.

The fields defined within the configuration files are the same fields defined in the
``NeighborlyConfig`` class. Here is an explanation of each field in YAML.

.. code-block:: yaml

    # Should the CLI restrict writing to the console
    verbose: <yes or no>
    # Seed used for random number generation
    seed: <int | string>
    # Prefab defining structure of character to character relationships
    relationship_schema: EntityPrefab
    # Starting date for world generation YYYY-MM-DD
    start_date: <date string> (
    # The number of years to simulate if no world_gen_end date is provided
    years_to_simulate: <int>
    # The amount of time to elapse between simulation steps.
    # This is specified by a number followed by the proper unit to specify
    # hours (hr), days (dy), months (mo), or years (yr).
    # For example, "2mo" is 2 months, and 6hr is 6 hours
    time_increment: <str>
    # Plugins to load before running
    plugins:
    # Accepts a list of strings or objects
    # Users can specify the module name for a plugin or a YAML map containing the
    # module name of the plugin and an optional path where the plugin can be found. The
    # path does not need to be specified if the plugin was installed using pip. If a path
    # is specified, Neighborly will look for the plugin on this path and attempt to import it.
    # The given path should either be an absolute file path or a path relative to the configuration
    # file's location. Additionally, users may include an options field, which is
    # a key-value map of parameters to pass to the plugin when setting it up. Plugin authors
    # should specify documentation on what parameters are available for each plugin.
    - <string> # python module name as if using an import statement
    - name: <string> # python module name as if using an import statement
        path: <string> (optional) # Path for where to find the python module/package if local
        options: # Key-value pair options to pass to the plugin when setting up the simulation
            <key>: <value>
            # ... other values
    # General key-value pairs with shared settings for systems and such
    settings:
        <key>: <value>
        ...
        # other values
