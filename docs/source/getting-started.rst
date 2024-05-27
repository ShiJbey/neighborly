.. _getting-started:

Getting Started
===============

Installation
------------

Neighborly is available to install from PyPI. Please use the following command to install the latest release. You may want to create a python virtual environment before installing. However, this is up to you.

.. code-block:: bash

    # (MacOS/Linux): Create and activate a Python virtual environment
    $ python3 -m venv venv
    $ source ./venv/bin/activate

    # (Windows): Create and activate a Python virtual environment
    $ python -m venv venv
    $ ./venv/Scripts/Activate

    # Install the latest neighborly release
    $ python -m pip install neighborly

We recommend that users specify a specific Neighborly release in their ``pyproject.toml`` or ``requirements.txt`` files. For example, ``neighborly==2.4.*``. Neighborly's function and class interfaces may change drastically between releases, and this will prevent errors from appearing in your code if an updated version of Neighborly breaks something you rely on.

Checking the Installation
-------------------------

Once installed, start the python interpreter and check that you can import neighborly without issues. You should be able to print the version number.

.. code-block:: bash

    $ python

    >>> import neighborly
    >>> neighborly.__version__
    # 3.0.0

Creating a sample simulation script
-----------------------------------

Now, let's create a simple simulation script using the content included with Neighborly. Copy the code below into a file named ``sample.py``.

.. code-block:: python

    from neighborly.config import LoggingConfig, SimulationConfig
    from neighborly.plugins import default_content
    from neighborly.simulation import Simulation
    from neighborly import inspection

    # First thing we do is create a simulation instance. This accepts a
    # SimulationConfig object that provides parameters for customizing the
    # behavior of the simulation.
    sim = Simulation(
        SimulationConfig(
            #seed="ACB123"
            logging=LoggingConfig(
                logging_enabled=True,
                log_to_terminal=False,
            ),
        )
    )

    # Neighborly is data-driven. We can load content from plugins to
    # customize how things are generated, and the behavior of characters.
    default_content.load_plugin(sim)

    # Runs the simulation for 50 years of time. Each timestep is one month
    # So, this results in 600 simulation steps.
    sim.run_for(years=50)

To interactively explore the generated content, run the script in interactive mode (passing ``-i`` to the python interpreter). The script will display a progress bar, and you will be able to interact with the simulation when it completes.

.. code-block:: bash

    python -i sample.py

Once complete, you will have access to the Python REPL. Neighborly provides an ``neighborly.inspection`` module that includes helpful utility functions that visualize simulation data in the terminal. Here is a list of the most used ones:

- ``inspection.inspect(sim, <Object UID>)`` - Show information about the object with the given UID
- ``inspection.list_settlements(sim)`` - Lists all settlements
- ``inspection.list_businesses(sim)`` - Lists all businesses
- ``inspection.list_characters(sim)`` - Lists all characters
- ``inspection.list_traits(sim)`` - Lists all traits
- ``inspection.list_job_roles(sim)`` - Lists all job_roles

.. code-block:: bash

    >>> inspection.list_settlements(sim)
    # === Settlements ===
    #   UID  Name          Population
    # -----  ----------  ------------
    #     1  Queensland           622

    >>> inspection.list_characters(sim)
    # UID    Name                       Age Sex     Species
    # ------ -------------------------- --- ------- -------
    # 88051  Ana Trippe                 62  FEMALE  Human
    # 92148  Melvin Prisk               63  MALE    Human
    # 92150  Aitana Bollom              56  FEMALE  Human
    # 92152  Julian Maidment             9  MALE    Human
    # 49146  Santino Durston            71  MALE    Human
    # ...

    # Let's inspect Ana Trippe using their UID
    >>> inspection.inspect(sim, 88051)

    # =======================
    # || Ana Trippe(88051) ||
    # =======================
    #
    # Active: True
    # Name: Ana Trippe(88051)
    #
    # === Character ===
    #
    # Name: 'Ana Trippe'
    # Age: 62 (ADULT)
    # Sex: FEMALE
    # Species: 'Human'
    # Resident of: 'Queensland(1)'
    #
    # === Stats ===
    #
    # Stat          Value
    # ------------  -------
    # lifespan      75[+0]
    # fertility     39[+0]
    # kindness      69[+10]
    # courage       40[-10]
    # stewardship   15[+5]
    # sociability   76[+0]
    # intelligence  71[+0]
    # discipline    36[+0]
    # charm         11[+0]
    #
    # === Traits ===
    #
    # ID                  Name                Duration    Timestamp    Description
    # ------------------  ------------------  ----------  -----------  ------------------------------------------------------------------------
    # cautious            Cautious            N/A         0135-08      This character is risk-averse and avoids dangerous situations.
    # ambitious           Ambitious           N/A         0135-08      This character is driven by ambition and seeks to achieve great success.
    # charitable          Charitable          N/A         0135-08      This character is generous and often helps others in need.
    # attracted_to_women  Attracted to Women  N/A         0135-08      This character experiences romantic attraction primarily to women.
    #
    # === Skills ===
    #
    # ID    Name    Level    Description
    # ----  ------  -------  -------------
    #
    # === Beliefs ===
    #
    # ID                      Description
    # ----------------------  ----------------------
    # women_are_attractive    Women are attractive.
    # men_are_not_attractive  Men are not attractive
    #
    # === Location Preferences ===
    #
    # ID    Description
    # ----  -------------
    #
    # === Member of Household ===
    #
    # Name: Household(91393)
    # Head of Household: Ana Trippe(88051)
    # Members: (Total 1)
    #         - Ana Trippe(88051)
    #
    # ...
