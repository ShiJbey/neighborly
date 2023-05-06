Settlements
===========

- ``Spawn Frequency``: The relative frequency of this business prefab in the
  simulation, compared to other business prefabs (defaults to 1).
- ``extends``: (Optional) The name of the Character prefab that this one extends
- ``tags``: (Optional) String tags for filtering
- ``max_instances``: Limits the number of instances of this prefab in a settlement
- ``min_population``: Requires that a certain population size be reached in a settlement
  before this prefab will spawn
- ``year_available``: Time locks the business prefab to only spawn after the simulation
  has reached a specified year
- ``year_obsolete``: Time locks businesses with a year that they will no longer spawn in
  the simulation
