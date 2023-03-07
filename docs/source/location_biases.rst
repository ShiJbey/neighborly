Location Biases
===============

We call the rules that affect character location choice, `LocationBiasRules`. Their
job is to bias which locations characters are likely to frequent. Rules are authored
as Python functions and registered with the simulation. An example rule is given
below. Bias rules usually have a precondition followed by a return statement with an
integer modifier representing how this rule will affect the location in question.

Its recommended to author your rules for inclusion instead of exclusion. So, think
of it as what traits, statuses, or components would make a character **more** likely
to frequent an establishment. Of course this is optional and you could always
create rules that display moral objections to an activity. A character that ``hates
alcohol`` should probably score places with ``drinking`` lower than other locations.

Location frequencies are first calculated when a character is added to a settlement and
recalculated on a regular interval. Usually, once per year.

.. code-block:: python


    def hates_alcohol_bias_rule(character: GameObject, location: GameObject) -> Optional[int]:
        if (
            character.has_component(HatesAlcohol)
            and location_has_activity(location, "drinking")
        ):
            return -5


The rule is added to the simulation using the following method call/decorator:

.. code-block:: python

    # You can add using the following
    sim.add_location_bias_rule(hates_alcohol_bias_rule)

    # Or you can use the decorator version directly on the
    # function definition
    @sim.location_bias_rule()
    def hates_alcohol_bias_rule(character, location):
        ...
