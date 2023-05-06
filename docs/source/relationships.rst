Relationships
=============

Relationships are at the core of agent-based social simulation along with social rules. In
Neighborly, relationships track how characters feel about other characters on different
facets such as friendship, romance, respect, and trust.

Relationships are GameObjects just like characters. So, they have their own set of components that
can be queried for and modified by systems.

Defining the schema
-------------------

Currently all relationships in Neighborly share the same core structure (components). This structure
is defined using a relationship schema within the ``NeighborlyConfig`` passed to the simulation.

The schema is just an prefab definition that asks the simulation author to define what components
should be present on a relationship GameObject at creation time. Usually, this includes naming the
various facets of the relationship. The two built-in facets are ``Romance`` and ``Friendship``.
Each facet has a max and min of 50 and -50, respectively. There can be as many or as few facets
as you wish. Each facet is a Component class that inherits from the ``RelationshipFacet`` class.

The simulation starts with a default relationship schema (see code below). Users are free to change
this schema, however, it may cause some content in plugins to throw errors or not function as
expected. So, be careful when removing any components from a schema.

.. code-block:: python

    # This is the default relationship schema
    NeighborlyConfig(
            relationship_schema={
                "components": {
                    "Friendship": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "Romance": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "InteractionScore": {
                        "min_value": -5,
                        "max_value": 5,
                    },
                }
            },
        ),
    )


Relationship Facets
-------------------

Relationship facets are the various axes of a relationship. Neighborly comes with three (3) default
facets. ``Romance`` tracks romantic attraction a character feels for another. ``Friendship`` tracks
platonic affinity from one character to another. And, ``InteractionScore`` is a special component
that tracks how much two characters should interact over the course of a month.

New facets can be created like any other component. Internally, they track three important scores

1. **Raw Value** - This is the raw score (sum of increments) retrieved with ``.get_raw_value()``.
2. **Clamped Value** - The score clamped between the min and max values given to the constructor.
   This value is retrieved using ``.get_value()``.
3. **Normalized Value** - This value returns a real number on the interval [0, 1.0], representing
   the total number of positive facet increments divided by the total number of positive and
   negative relationship increments. This is accessed using ``.get_normalized_value()``.

.. code-block:: python

    from neighborly import Neighborly
    from neighborly.core.relationship import RelationshipFacet


    class Trust(RelationshipFacet):
        pass


    class Respect(RelationshipFacet):
        pass

    sim = Neighborly()

    # The new facets need to be registered to be used with the schema
    sim.world.register_component(Trust)
    sim.world.register_component(Respect)

    # Add the new facets to the schema
    sim.config.relationship_schema.components["Trust"] = {
        "min_value": -100,
        "max_value": 100,
    }

    sim.config.relationship_schema.components["Respect"] = {
        "min_value": -100,
        "max_value": 100,
    }


Creating new relationships
--------------------------

Relationship instances are created between characters by using the ``add_relationship`` or
``get_relationship`` utility functions. You need to have references to two (2) GameObjects to
form a new relationship. Technically, the GameObjects do not need to be characters. They could
be organizations, inanimate objects, or characters referencing themselves.

.. code-block:: python

    from neighborly.core.relationship import add_relationship, get_relationship, has_relationship
    # ... other set up code

    # You need to have references to two GameObjects to form a relationship.
    # There is not a requirement that
    alice = sim.world.spawn_gameobject()
    hatter = world.spawn_gameobject()

    hatter_to_alice = add_relationship(hatter, alice)

    # The get_relationship function will create a new relationship if one does not exist
    # So this is probably the function you want to use most
    alice_to_hatter = get_relationship(alice, hatter)

    assert has_relationship(alice, hatter)


Modifying relationship facets
-----------------------------

Sometimes character relationship facets need to be updated to reflect event that have transpired
between characters. Or, we may want to manually apply initial conditions to the relationship
facets. We do this by getting a reference to the desired facet and using the increment function
on them.

.. code-block:: python

    # Set the base value
    alice_to_hatter.get_component(Friendship).set_base(5)
    alice_to_hatter.get_component(Trust).set_base(2)

    # Increment the value with a positive or negative value
    alice_to_hatter.get_component(Friendship).increment(-3)

Relationship Statuses
---------------------

Much like how characters can have statuses applied to them, Relationships can also have statuses.
Relationship statuses track things about the relationship that may or may not change at runtime.
Statuses can track familial relationships, marriages, dating situationships, crushes, debts and
more. Since statuses are components, they can be queried for in systems using
``world.get_components(...)``.

.. code-block:: python

    class OwesMoney(RelationshipStatus):

        def __init__(self, amount: int = 0) -> None:
            self.amount: int = amount

    add_relationship_status(
        alice,
        hatter,
        OwesMoney(50)
    )
