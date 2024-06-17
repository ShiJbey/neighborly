from typing import Optional
from neighborly.components.shared import Modifier, ModifierManager
from neighborly.ecs import GameObject


def add_modifier(target: GameObject, modifier: Modifier) -> None:
    """Add a modifier to a GameObject."""

    target.get_component(ModifierManager).add_modifier(modifier)

    modifier.apply(target)


def remove_modifier(target: GameObject, modifier: Modifier) -> bool:
    """Remove a modifier from a GameObject.

    Returns
    -------
    bool
        True if removed successfully.
    """

    success = target.get_component(ModifierManager).remove_modifier(modifier)

    if success:
        modifier.remove(target)

    return success


def remove_modifiers_from_source(target: GameObject, source: Optional[object]) -> bool:
    """Remove all modifiers from a given source.

    Returns
    -------
    bool
        True if any modifiers were removed
    """
    modifier_manager = target.get_component(ModifierManager)

    modifiers_to_remove = [
        m for m in modifier_manager.modifiers if m.get_source() == source
    ]

    for m in modifiers_to_remove:
        remove_modifier(target, m)

    return len(modifiers_to_remove) > 0
