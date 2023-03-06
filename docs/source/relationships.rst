Relationships
=============

Relationships are at the core of agent-based social simulation. In Neighborly,
relationships track how characters feel about other characters on different
axes, changes in relationship status, and other informational tags.

Relationships are have two main components. The first is a set of various
relationship stats. These are specified by the user (explained below) and
can be used to represent things like platonic feelings, romantic feelings,
and trust.

Defining the schema
-------------------

Below is an example relationship schema. The RelationshipSchema is
responsible for telling the simulation how new relationship instances
are to be configured. In this case there, are three stats within this
relationship: Friendship, Romance, and Trust. Each axis has a max and min
of 50 and -50, respectively. There can be as many or as few stats tracked
as you wish, and there are no rules for names. However, you must be
consistent in referencing each stat within other simulation code.

Something special to note here is the ``changes_with_time`` parameter.
When it is set to ``True``, that relationship stat will change automatically
without two characters explicitly interacting. Since Neighborly skips large
intervals of time, we needed a way to interpolate the relationship value
to give the impression that two characters most likely interacted during
that time.

.. code-block:: python

    NeighborlyConfig(
        # ... other config parameters
        relationship_schema=RelationshipSchema(
            stats={
                "Friendship": RelationshipStatConfig(
                    min_value=-50, max_value=50, changes_with_time=True
                ),
                "Romance": RelationshipStatConfig(
                    min_value=-50, max_value=50, changes_with_time=True
                ),
                "Trust": RelationshipStatConfig(
                    min_value=-50, max_value=50, changes_with_time=False
                ),
            }
        ),
    )


Creating new relationships
--------------------------

Relationship instances are created between characters by using the
``add_relationship`` utility function.

.. code-block:: python

    alice = world.spawn_gameobject()

    hatter = world.spawn_gameobject()

    alice_to_hatter = add_relationship(alice, hatter)

    alice_to_hatter["Friendship"] += 5
    alice_to_hatter["Trust"] += 2

    # Attempting to access a stat not specified in the
    # schema will give an error
    alice_to_hatter["Attraction"] += -2 # throws RelationshipStatNotfound error

Updating the stats
------------------

Relationship stats can be accessed by indexing into a ``Relationship``
instance using the name of the stat as specified in the schema.

.. code-block:: python

    relationship =
