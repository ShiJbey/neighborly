Location Biases
===============

We call the rules that affect character location choice, `LocationBiasRules`. Their
job is to bias which locations characters are likely to frequent. Rules are authored
as Python functions and registered with the simulation. An example rule is given
below. Bias rules usually have a precondition followed by a return statement with an
integer modifier representing how this rule will affect the location in question.

Currently, the probability of a character frequenting a location is calculated using a softmax of
the scores of all the locations within the settlement. Locations with a higher total score will
have a higher probability of being selected as a place that the character frequents.

Location frequencies are first calculated when a character is added to a settlement and
recalculated on a regular interval. Usually, once per year.

Authoring new rules
-------------------

Its recommended to author your rules for inclusion instead of exclusion. So, think
of it as what traits, statuses, or components would make a character more or less likely
to frequent an establishment. For example, you could
create rules that display moral objections to an activity, such as character that ``hates
alcohol`` should score places with ``drinking`` lower than other locations.

.. code-block:: python


    def hates_alcohol_bias_rule(character: GameObject, location: GameObject) -> Optional[int]:
        if (
            character.has_component(HatesAlcohol)
            and location_has_activity(location, "drinking")
        ):
            return -5

Adding new rules to the simulation
----------------------------------

Rule authors can add their location bias rules to the simulation using either the
`LocationBiasRules.add(...)` classmethod, or the `@location_bias_rule` decorator function.

.. code-block:: python

    from neighborly.decorators import location_bias_rule

    # You can add using the following
    LocationBiasRules.add(hates_alcohol_bias_rule)

    # Or you can use the decorator version directly on the
    # function definition
    @location_bias_rule()
    def hates_alcohol_bias_rule(character, location):
        ...
