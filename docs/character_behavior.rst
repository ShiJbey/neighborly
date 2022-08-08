Character Behavior
------------------

Character behavior is executed two ways.

The first and primary way is life events. Life events are triggered when
there are characters or other GameObjects that fit the specifications
for the roles defined by the event. You can think of Roles like roles in
a theatrical performance. GameObjects are cast into these roles if they
meet the requirements of the role.

When all roles are successfully casted, the event may trigger some additional
code to run that makes changes to the state of the simulation. This code

When an event fires, the simulation makes a record of it and the GameObjects
casted into the roles. We can use this information later for story sifting or
debugging.

What is the difference between behaviors and events?
====================================================

Events immediately create a new event that is recorded in the
simulation's history. They assume that when all the roles have
been casted, there are no additional checks that could veto the
event or directly trigger cascading events.

Behaviors are an abstraction built on behavior trees. Like events,
they cast an initial set of characters before executing the tree
logic. These characters are stored in a roles array within the
behavior tree's blackboard. Each leaf node in the tree
receives the current blackboard and world instances an parameters.
Nodes are responsible for performing checks and executing **Actions**.

**Reserved Blackboard Keys**

* "roles" - List of roles cast before and during execution
* "trigger" - Previous BehaviorTree/Action that triggered this (optional)
* "" -
