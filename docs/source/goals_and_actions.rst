Goals and Actions
=================

Goals are how we implement intentional character behavior. Goals are represented as behavior tree
nodes that can have sub goals, and action nodes that help to accomplish the original goal.

Each timestep, during the "goal-suggestion" phase of the update loop, systems can add Goals to
characters' ``Goals`` component. These goals are sampled using weighted-random selection, where
goal weights are utility scores associated with goals.
