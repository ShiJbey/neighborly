Neighborly's Event Architecture
===============================

Background
----------

Event-Driven programming is a software architecture approach that allows particular bits
of code to run in response to something happening in another part of the code.
It adds an element of reactivity to the code without enforcing hard coupling between
objects. If you've done any JavaScript web programming, then you are probably no
stranger to event-driven programming.

Events in Neighborly
--------------------

In Neighborly, events serve multiple purposes. The primary purpose of events is to serve as
potential content when constructing stories. The second purpose is to allow simulation
authors to trigger functions in reaction to things happening to the characters.

List of Neighborly Events
-------------------------

- ``join-settlement``
- ``leave-settlement``
- ``business-open``
- ``business-close``
- ``new-settlement``
