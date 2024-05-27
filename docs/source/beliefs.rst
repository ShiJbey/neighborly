.. _beliefs:

Beliefs
=======

Beliefs are cultural or personal beliefs a character holds about society that affect how they feel about other characters. They are good for modifying character behavior and expressing their personality. The belief system replaces the old social rule system. Beliefs have the same general structure as social rules. However, they are only applied to outgoing relationships. Thus, they represent beliefs that one agent has about other people. These beliefs then apply various effects to outgoing relationships that meet specified preconditions.

Simulation creators specify new :py:class:`~neighborly.defs.base_types.BeliefDef` s in YAML/JSON, which are transformed into :py:class:`~neighborly.components.beliefs.Belief` class instances when initializing the simulation. Various traits can apply these beliefs by adding the :py:class:`~neighborly.effects.effects.AddBelief` effect to their list of effects along with the ID of the belief. We track all the specific beliefs a character holds using the :py:class:`~neighborly.components.beliefs.HeldBeliefs` component. We use these and global beliefs in the :py:class:`~neighborly.libraries.BeliefLibrary` to determine modifiers when evaluating relationships. All beliefs affecting a relationship are tracked using their :py:class:`~neighborly.components.beliefs.AppliedBeliefs` component.

Defining custom beliefs
-----------------------

Data Fields
^^^^^^^^^^^

- **definition_id** -- A unique ID for the belief.
- **description** -- A text description of this belief.
- **preconditions** -- Preconditions checked against relationships.
- **effects** -- Effects to apply to relationships.
- **is_global** -- Do all characters automatically hold this belief.

Example Belief Definitions
^^^^^^^^^^^^^^^^^^^^^^^^^^

YAML

.. code-block:: yaml

    - definition_id: "men_are_not_attractive"
      description: "Men are not attractive"
      preconditions:
        - type: GenderRequirement
          gender: "male"
          target: target
      effects:
        - type: AddStatBuff
          stat: romance
          amount: -15

    # Other belief definitions

JSON

.. code-block:: javascript

    [
        {
            "definition_id": "men_are_not_attractive",
            "description": "Men are not attractive",
            "preconditions": [
                {
                    "type": "GenderRequirement",
                    "gender": "male",
                    "target": "target"
                }
            ],
            "effects": [
                {
                    "type": "AddStatBuff",
                    "stat": "romance",
                    "amount": -15
                }
            ]
        },
        // Other social rules
    ]

Python

.. code-block:: python

    BeliefDef(
        definition_id="men_are_not_attractive",
        description="Men are not attractive",
        preconditions=[
            {
                "type": "GenderRequirement",
                "gender": "male",
                "target": "target"
            }
        ],
        effects=[
            {
                "type": "AddStatBuff",
                "stat": "romance",
                "amount": -15
            }
        ]
    )

Loading beliefs from external files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Above, we provide three ways of creating belief definitions for your simulation. The YAML and JSON methods require you to load the definitions from external files.

.. code-block:: python

    from neighborly.loaders import load_beliefs
    from neighborly.simulation import Simulation


    sim = Simulation()

    load_beliefs(sim, "path/to/beliefs_file")

    # ...


Loading beliefs specified in Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Belief definitions created directly in Python need to be added to the ``BeliefLibrary``. The belief library is a global resource on the simulations World instance. The sample code below shows you how to do this.


.. code-block:: python

    from neighborly.libraries import BeliefLibrary
    from neighborly.simulation import Simulation


    sim = Simulation()

    belief_library = sim.world.resources.get_resource(BeliefLibrary)

    belied_library.add_definition(
        BeliefDef(
            # definition content
        )
    )

    # ...
