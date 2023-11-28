.. _design-tips:

Design Tips and FAQ
===================

When should I use a new component vs. a new trait?
--------------------------------------------------

Create a custom component if there is GameObject-specific data that you need to track. Traits are helpful for flexibly authoring effects but cannot hold stateful information.

If you want the best of both components and traits, first create a custom component, then have the component add traits to GameObject within their :py:meth:`neighborly.ecs.Component.on_add` method. For example, in the code below, we have a ``Vampire`` component that tracks vampire-specific data and adds a ``vampirism`` trait that can define specific effects like making characters immortal or buffing existing traits. Assume we load the ``vampirism`` trait from an external data file.

.. code-block:: python

    class Vampire(Component):
        """Tracks information about a vampire."""

        __slots__ = ("humans_bled",)

        humans_bled: int
        """The number of human's they have feasted on."""

        def __init__(self):
            super().__init__()
            self.humans_bled = 0

        def on_add(self):
            add_trait(self.gameobject, "vampirism")

        def remove_trait(self):
            remove_trait(self.gameobject, "vampirism")

.. code-block:: yaml

    vampirism:
        display_name: Vampirism
        description: This character is a vampire
        effects:
            # This effect makes them unable to die from old age because
            # their life decay becomes zero
            - type: StatBuff
              stat: health_decay
              amount: -5000
            # This effect makes them more less friendly toward humans
            - type: AddSocialRule
              preconditions:
                - type: TargetHasTrait
                  trait: human
              effects:
                - type: StatBuff
                  stat: reputation
                  amount: -15


When should I create new systems?
---------------------------------

Consider creating a new system when you want a simulation mechanic to happen or be checked during every timestep (tick) of the simulation. For instance, health stats are decayed every tick, and character pregnancies are implemented as a system with custom components to ensure that pregnancies take the proper amount of time.
