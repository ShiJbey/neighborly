Statuses
========

Statuses represent temporary states associated with a GameObject. We apply statuses to
everything ranging from characters to businesses to relationships. Statuses are applied
at runtime and are not applied at entity creation time.

Status components are a all components that derive from the ``StatusComponent`` class.
They operate the same as other components, and allow you to query for them within
systems when using the ``world.get_components()`` function.

GameObject that use statuses should have a ``StatusManager`` component attached that
tracks what statuses are active on the character. This is how the simulation is able
to determine which components are statuses.

Statuses should only be modified using the following utility functions. They ensure
that the ``StatusManager`` is kept up to date when applying or removing status
components. By default, when a status is applied, they are timestamped with the
current date of the simulation.

- ``add_status(gameobject, status)``
- ``remove_status(gameobject, status)``
- ``clear_statuses(gameobject)``

Examples of statuses
--------------------

**Examples of character statuses**

- ``Unemployed``
- ``Pregnant``
- ``Retired``

**Examples of relationship statuses**

- ``Dating``
- ``Married``
- ``CoworkerOf``

**Examples of business statuses**

- ``OpenForBusiness``
- ``ClosedForBusiness``


.. code-block:: python

    sim = Neighborly()

    jessie = sim.world.spawn_gameobject(name="Jessie")
    chris = sim.world.spawn_gameobject(name="Chris")

    add_status(jessie, Unemployed())

    add_status(get_relationship(jessie, chris), FriendOf())
    add_status(get_relationship(chris, jessie), FriendOf())

    add_status(get_relationship(jessie, chris), SecretCrush())

    assert get_relationship(jessie, chris).has_component(FriendOf)
    assert get_relationship(jessie, chris).has_component(SecretCrush)
