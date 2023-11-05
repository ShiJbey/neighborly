.. _businesses:

Businesses
==========

Businesses are places where characters work. They are also "hubs" of social activity where characters can meet coworkers and other people who frequent the establishment. Below is an example of a business definition in JSON. Neighborly uses this data to create Business GameObjects.

Defining businesses
-------------------

Business definitions should be placed in JSON data files with other Business definitions. Below are the default fields for a business definition, along with an example definition.

Business Definition Fields
--------------------------

- ``display_name``: Regular text name or Tracery string used to generate a name for the business.
- ``spawn_frequency``: An integer frequency of this business type spawning in a district relative to other business types that can spawn.
- ``max_instances``: The maximum instances of this business type that are allowed to coexist within the same district.
- ``min_population``: The minimum settlement population required for this business type to spawn.
- ``owner_role``: The string ID of the JobRole that the owner will have.
- ``employee_roles``: JobRole IDs of employee jobs mapped to the max number of that role available at a business.

An example definition
---------------------

Below is an example of a Blacksmith Shop. It spawns with a primary frequency of one, and only two Blacksmith Shops can operate simultaneously.

.. code-block:: json

    {
        "blacksmith_shop": {
            "name": "Blacksmith Shop",
            "spawn_frequency": 1,
            "max_instances": 2,
            "min_population": 10,
            "owner_role": "blacksmith",
            "employee_roles": {
            "blacksmith_apprentice": 1
            }
        }
    }

Loading definitions into the simulation
---------------------------------------

Business definitions should be placed in JSON files with other business definitions. To load all the business definitions within a single file, use the ``neighborly.loaders.load_businesses(...)`` helper function. An example usage can be seen in the example code for instantiating businesses.

Instantiating business instances
--------------------------------

Business instantiation is handled by the ``SpawnNewBusinessesSystem``. However, if users need to manually instantiate new business types, there is a ``neighborly.helpers.business.create_business(...)`` function. This function interfaces with the `BusinessLibrary` and instantiates a new business using an existing definition. For example, creating a new blacksmith shop would look like the following:

.. code-block:: python

    from neighborly.loaders import *
    from neighborly.helpers.settlement import create_settlement, create_district
    from neighborly.helpers.business import create_business

    sim = Simulation()

    load_districts(sim, "districts.json")
    load_settlements(sim, "settlements.json")
    load_businesses(sim, "businesses.json")
    load_characters(sim, "characters.json")
    load_residences(sim, "residences.json")
    load_job_roles(sim, "job_roles.json")

    sim.initialize()

    settlement = create_settlement(sim.world, "basic_settlement")

    district = create_district(sim.world, settlement, "entertainment_district")

    blacksmith_shop = create_business(sim.world, district, "blacksmith_shop")


Advanced: creating new definition types
---------------------------------------

By default, all business definitions are instantiated using the built-in ``DefaultBusinessDef`` class. This class inherits from the ``BusinessDef`` abstract base class and provides functionality for initializing a new Business GameObject using the definition data. There may be cases when users want to do something special with the business definitions, such as adding new components at instantiation time or overriding the name generation to use an LLM instead of Tracery. In these cases, users should create their own business definition class by inheriting from ``BusinessDef`` or ``DefaultBusinessDef``. Then, they should ensure that their business definition type is added to the BusinessLibrary using the ``BusinessLibrary.add_definition_type()`` method. This method accepts as parameters the business definition class. It has two optional parameters for setting an alias name for the new type and setting this type as the default used to load JSON data.

Within the business JSON file, users can specify the business definition type to use when loading an entry by adding a ``"definition_type": "class name or alias"`` entry to the JSON definition of a business. When this field is omitted from the definition, the system defaults to use whichever definition is currently set as the
default. This feature allows users to overwrite the default behavior of how businesses are instantiated without needing to update all their content or the content contained within third-party plugins.

Below is a pseudocode example of this process. Remember that ``BusinessDef`` is an [``attrs``](https://www.attrs.org/en/stable/index.html) dataclass. So, attribute variables are declared and type-hinted in the main class body, and there is no ``__init__()`` method.

.. code-block:: python

    from neighborly.defs.base_types import BusinessDef
    from neighborly.libraries import BusinessLibrary

    class CustomBusinessDef(BusinessDef):
    """Custom business definition type.

    BusinessDef subclasses have to override two abstract methods, initialize()
    and from_obj(). Subclasses are free to add new instance variables to.
    """

    def initialize(self, district: GameObject, business: GameObject) -> None:
        """Initialize a business' components using the definition data.

        Parameters
        ----------
        district
            The district where the business resides.
        business
            The business to initialize.
        """
        # Do something ...

        def from_obj(cls, obj: dict[str, Any]) -> BusinessDef:
        """Create a business definition from a data dictionary

        Parameters
        ----------
        obj
            A dictionary of configuration settings.

        Returns
        -------
        BusinessDef
            An instance of this business definition
        """
        # Do something ...


.. code-block:: python

    from neighborly.libraries import BusinessLibrary

    sim = Simulation()

    library = sim.world.resources.get_resource(BusinessLibrary)

    # The following call adds the CustomBusinessDef as an eligible definition to
    # use when constructing business instances, sets its definition_type alias to
    # "custom", and sets it as the default definition type to use when JSON entries
    # do not include the "definition_type" attribute.
    library.add_definition_type(CustomBusinessDef, alias="custom", set_default=True)


When loading the following JSON business definitions, both would use the ``CustomBusinessDef`` class because it has been set as the default business definition.

.. code-block:: json

    {
        "example_biz_1": {
            "definition_type": "custom",
            "owner_role": "Owner"
        },
        "example_biz_2": {
            "owner_role": "Owner"
        }
    }

Job Roles
---------

Job Roles define the requirements and effects associated with various occupations that characters can have while working in the settlement. Like other pieces of data, Job Roles can be defined using JSON and loaded into the simulation before running. Job Roles can be shared across business types to save authoring time. Below are the traits associated with job roles.

- ``definition_id``: The ID of this job role (unique among other roles).
- ``name``: A display name used for debugging and generating character descriptions
- ``job_level``: The general amount of prestige or socioeconomic status associated with the job role.
- ``requirements``: A list of precondition functions
- ``effects``: A list of effects applied when the character gains an occupation with this role.
- ``monthly_effects``: list of effects applied every month the character holds the job. (These effects are not reversible).

Below are examples of a Blacksmith and Blacksmith Apprentice job roles:

.. code-block:: json

    {
        "blacksmith": {
            "display_name": "Blacksmith",
            "job_level": 2,
            "requirements": [
                {
                    "type": "SkillRequirement",
                    "skill": "blacksmithing",
                    "level": 50
                }
            ],
            "monthly_effects": [
                {
                    "type": "IncreaseSkill",
                    "skill": "blacksmithing",
                    "amount": 1
                }
            ]
        },
        "blacksmith_apprentice": {
            "display_name": "Blacksmith Apprentice",
            "job_level": 1,
            "monthly_effects": [
                {
                    "type": "IncreaseSkill",
                    "skill": "blacksmithing",
                    "amount": 3
                }
            ]
        }
    }


How do I use Job Roles?
-----------------------

Job roles are referenced within Business definitions. Take the Blacksmith Shop business definition below. notice there are two places where we use job roles -- the ``owner_role`` field and the ``employee_roles`` field.

.. code-block:: json

    {
        "blacksmith_shop": {
            "name": "Blacksmith Shop",
            "spawn_frequency": 1,
            "max_instances": 2,
            "min_population": 10,
            "owner_role": "blacksmith",
            "employee_roles": {
                "blacksmith_apprentice": 1
            }
        }
    }
