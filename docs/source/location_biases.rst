Location Biases
===============

Activities add an additional layer of nuance to how characters choose where they want to
go. In a lower-fidelity simulation like Neighborly, we use activities to calculate scores
for how likely characters are to frequent a location. For example, a character that has
a *Lazy* trait might be more likely to frequent a location with *Relaxing* as an
activity.

Authoring activities
--------------------

Creating new activities is really easy. In-fact, there is nothing special that you,
as a simulation designer need to do other than specify the activity as being offered
by a location. You do this inside the prefab definition for a location. Activity names
are case-insensitive. Internally, the simulation tracks all the different activities
specified by locations.

Below is an example of a ``Forest`` location prefab. Please note that all available
activities are specified under the ``Activities`` component.

.. code-block:: yaml

    # forest.prefab.yaml
    # YAML definition of a Forest location prefab
    name: Forest
    components:
        Location: {} # curly braces denote an empty map
        StatusManager: {}
        Activities:
            activities:
                - foraging
                - camping
                - hunting

You can then load the prefab definition into the simulation:

.. code-block:: python

    from neighborly import Neighborly
    from neighborly.utils import spawn_location_prefab
    from neighborly.loaders import load_location_prefab

    sim = Neighborly()

    load_location_prefab(sim, "forest.prefab.yaml")

    forest = spawn_location_prefab(sim, "Forest")

The next step in the process is to create some rules that govern what types of
characters will frequent this location. We go over location bias rules below.

Authoring Location Bias Rules
-----------------------------

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
