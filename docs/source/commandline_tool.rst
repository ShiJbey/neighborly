Commandline Tool
================

Neighborly includes a commandline interface (CLI) tool that runs an instance of a 
simulation and may be customized with optional settings supplied in a configuration
file. The CLI will set any needed parameters, load specified plugins, run the
simulation, and export the simulation data to a JSON file.

By default, the CLI runs a built-in clone of 
`Talk of the Town <https://github.com/james-owen-ryan/talktown>`_, another social 
simulation.

Users can customize the CLI's behavior by specifying command-line arguments or
using a configuration file. To view the complete list of command-line arguments,
please use ``neighborly --help`` or ``python -m neighborly --help``.

If users need to do something more complex or they would like to consolidate their
simulation into a single file, we recommend using Neighborly as a library. Examples of
this style of usage can be found in the 
`samples folder <https://github.com/ShiJbey/neighborly/tree/main/samples>`_.

Configuration files
-------------------

Neighborly accepts YAML and JSON as configuration files. By default, the CLI
will look for any of the following files to be present in the current working 
directory.

These are listed in order of precedence:

- neighborly.config.yaml
- neighborly.config.yml
- neighborly.config.json

Users can tell Neighborly to use a different configuration file by using
``neighborly -c path/to/config`` or ``neighborly --config path/to/config``.

The fields defined within the configuration files are the same fields defined in the
``NeighborlyConfig`` class. Here is an explanation of each field in YAML.

.. code-block:: yaml

    # Should the CLI restrict writing to the console
    verbose: <yes or no>
    # Seed used for random number generation
    seed: <int | string>
    # Prefab defining structure of character to character relationships
    relationship_schema: EntityPrefab
    # Starting date for world generation DD/MM/YYYY or YYYY-MM-DDTHH:00 ISO 8061 format
    start_date: <string>
    # The number of years to simulate if no world_gen_end date is provided
    years_to_simulate: <int>
    # The amount of time to elapse between simulation steps.
    # This is specified by a number followed by the proper unit to specify
    # hours (hr), days (dy), months (mo), or years (yr).
    # For example, "2mo" is 2 months, and 6hr is 6 hours
    time_increment: <string>
    # Plugins to load before running
    plugins:
    # Accepts a list of strings or objects
    # Users can specify the module name for a plugin or a YAML map containing the
    # module name of the plugin and an optional path where the plugin can be found. The
    # path does not need to be specified if the plugin was installed using pip. If a 
    # path is specified, Neighborly will look for the plugin on this path and attempt 
    # to import it. The given path should either be an absolute file path or a path 
    # relative to the configuration file's location. Additionally, users may include an 
    # options field, which is a key-value map of parameters to pass to the plugin when 
    # setting it up. Plugin authors should specify documentation on what parameters are 
    # available for each plugin.
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
