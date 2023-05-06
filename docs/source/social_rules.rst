Social Rules
============

Social rules are one of the core elements Neighborly's social simulation. They allow characters
to determine how they feel about each other based on their current components and event histories.
They are run when characters initially meet and are recalculated occasionally.

Some concepts that can encoded using these rules are differential romance based on age,
a penalty for romances among family members, sexual preferences, friendship preferences, affinity
for similar ethnic groups, and more.

Authoring Rules
---------------

Below is an example of a social rules that calculates an romance modifier value based on the number
of shared virtues between characters. All social rules take two characters as parameters, a subject
and a target that we are calculating feelings toward. Rules then return a dictionary that maps
a relationship facet type (Romance, Friendship, Respect, etc.) to an integer modifier. Within the
function users are free to calculate modifiers how they see fit.


.. code-block:: python

    def romance_boost_from_shared_virtues(
        subject: GameObject, target: GameObject
    ) -> Dict[Type[RelationshipFacet], int]:
        """Characters with shared high/low virtues gain romance points"""

        if not subject.has_component(Virtues) or not target.has_component(Virtues):
            return {}

        subject_virtues = subject.get_component(Virtues)
        target_virtues = target.get_component(Virtues)

        shared_likes = set(subject_virtues.get_high_values()).intersection(
            set(target_virtues.get_high_values())
        )
        shared_dislikes = set(subject_virtues.get_low_values()).intersection(
            set(target_virtues.get_low_values())
        )

        return {Romance: len(shared_likes) + len(shared_dislikes)}

Adding rules to the simulation
------------------------------

Method 1: Register with the SocialRules class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Social rules can be registered directly within the `SocialRules` class either within a plugin's
setup function or anywhere before the start of the simulation. The `SocialRule.add(...)` method
takes a SocialRule reference and a text description as input. `SocialRules` is a static class that
acts as a repository for social rules

.. code-block:: python

    SocialRules.add(romance_boost_from_shared_virtues, "Boost from shared virtues")

Method 2: Use the decorator
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're authoring your simulation within a single Python script, you can take advantage of
Neighborly's built-in decorators to simplify adding content.

.. code-block:: python

    from neighborly.decorators import social_rule

    # Here we use the social_rule decorator which automatically registers the social rule
    # and requires that we give it a text description
    @social_rule("Romance boost from shared virtues")
    def romance_boost_from_shared_virtues(
        subject: GameObject, target: GameObject
    ) -> Dict[Type[RelationshipFacet], int]:
        """Characters with shared high/low virtues gain romance points"""

        if not subject.has_component(Virtues) or not target.has_component(Virtues):
            return {}

        subject_virtues = subject.get_component(Virtues)
        target_virtues = target.get_component(Virtues)

        shared_likes = set(subject_virtues.get_high_values()).intersection(
            set(target_virtues.get_high_values())
        )
        shared_dislikes = set(subject_virtues.get_low_values()).intersection(
            set(target_virtues.get_low_values())
        )

        return {Romance: len(shared_likes) + len(shared_dislikes)}

    # ... The rest of the simulation script
