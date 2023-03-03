Businesses
==========

Businesses are locations within the town that house places where people work. They add
an additional layer of narrative richness to the simulation by fleshing out the type
of settlement that characters live in. Meeting and interacting with people at work is
one of the main ways that relationships grow. Characters spend a good amount of time in
close social proximity with their coworkers.

Services
--------

Services are things that the business offers customers. They may be used to cast
businesses into roles within events that require a particular business. For example,
a `ChildBirthEvent` may choose a to record a hospital where the child was born. To do
this we could search for all game objects with a ``Services`` component then filter for
``Services`` containing the *"hospital"* service. You can easily do this using the
``find_places_with_services(world, *services)`` utility function.

.. code-block:: python

    hospitals = find_places_with_services(world, "hospital")
    print(hospitals)

At this point you may be wondering how you add services to a business. This is done
within the entity prefab file. Add a "Services" entry under the *components* map and
enter the list of services. These are case-insensitive, but typos and misspellings are
not caught by the system. So, be sure to be consistent in your naming conventions.
Please note that the "Service" entry (capital *S*) has a keyword argument "service"
(lowercase *s*).

.. code-block:: yaml

    name: "business::hospital"
    extends: "business::default"
    config:
        owner_type: Doctor
    components:
        Business:
            name: "Hospital"
            employees:
                Doctor: 2
                Nurse: 3
                Secretary: 1
        # Services go here!!
        Services:
            services:
                - hospital
                - emergency_medical




.. toctree::
    :maxdepth: 2
    :caption: Contents:

    installation.rst
    working_with_ecs.rst
    relationships.rst
    event_driven_architecture.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
