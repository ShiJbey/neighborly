.. _stats:

Stats
=====

.. attention:: This page needs to be updated for version 3

Stats in Neighborly serve the same purpose they do in RPGs. Track numerical attributes associated with gameobjects. For example, all characters have stats to track, among other things, fertility, lifespan, stewardship, and sociability. Stats are tracked using individualized component instances, and they are collectively organized by the :py:class:`~neighborly.components.stats.Stats` component.

Defining custom stats
---------------------

Each stat component is a subclass of :py:class:`~neighborly.components.stats.StatComponent`. The code below shows how the :py:class:`~neighborly.components.stats.Lifespan` component is defined. It is essential that the ``__stat_name__`` class variable be defined when creating custom components. This name is how stats are referenced
when using stat buff effects or accessing a stat using :py:function:`~neighborly.helpers.stats.get_stat`.

.. code-block:: python

    class Lifespan(StatComponent):
    """Tracks a GameObject's lifespan."""

    __stat_name__ = "lifespan"

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value, (0, 999_999), True)

Adding custom stats to characters
---------------------------------

When creating a stat we probably want to includ it in the components of every character when they are created.
