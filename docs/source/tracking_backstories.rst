Tracking Backstories
====================

As characters progress through the simulation, they will have the opportunity
to engage in various events. These events make up their personal backstories
and we track this data for every character in the simulation.

Event History
-------------

All the events that have occurred in the simulation are stored in a shared,
``AllEvents`` resource within the World instance. Each character is given an
``EventHistory`` component that tracks the IDs of events that the character was
a part of. You can use these IDs to retrieve the events from the shared resource
using the ``get_events_for()`` utility function and pass the character as a
parameter.
