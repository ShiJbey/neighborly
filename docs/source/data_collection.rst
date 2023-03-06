Data collection
===============

Many agent-based modeling (ABM) tools feature some methods for collecting agent data for processing
or visualization. Neighborly lets users collect simulation data into tables that can be written to
files and processed using popular Python data-science libraries like Pandas. Neighborly's particular
implementation is heavily inspired by `Mesa <https://mesa.readthedocs.io/en/stable/>`_,
another python-based ABM tool.

How to collect data
-------------------

Data collection starts with creating a new table before the simulation starts.

.. code-block:: python

    sim.world.get_resource(DataCollector).create_new_table(
        "wealth", ("uid", "name", "timestamp", "money")
    )

You can then write rows of data to this table. This can be done regularly within a system or only
when certain events occur.

.. code-block:: python

    sim.world.get_resource(DataCollector).add_table_row(
        "wealth",
        {
            "uid": guid,
            "name": game_character.full_name,
            "timestamp": timestamp,
            "money": money,
        },
    )

Please see the data collection sample in the `samples` directory.
