Locations
=========

Locations are places that characters can travel to and frequent. They are the places
where characters are able to socialize. 

Activities add an additional layer of nuance to how characters choose where they want to
go. In a lower-fidelity simulation like Neighborly, we use activities to calculate scores
for how likely characters are to frequent a location. For example, a character that has
a *Lazy* trait might be more likely to frequent a location with *Relaxing* as an
activity.

Activities
----------

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
