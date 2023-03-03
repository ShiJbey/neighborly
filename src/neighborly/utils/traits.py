from typing import Type, TypeVar

from neighborly.core.ecs import GameObject
from neighborly.core.traits import TraitComponent, TraitManager

_T = TypeVar("_T", bound=TraitComponent)


def add_trait(character: GameObject, trait: TraitComponent) -> None:
    """Add a trait to a character

    Parameters
    ----------
    character: GameObject
        The character to add the trait to
    trait: TraitComponent
        The trait to add
    """
    character.get_component(TraitManager).add(type(trait))
    character.add_component(trait)


def get_trait(character: GameObject, trait_type: Type[_T]) -> _T:
    """Get a trait from a character

    Parameters
    ----------
    character: GameObject
        The character to get the trait from
    trait_type: Type[_T]
        The type of trait to get

    Returns
    -------
    _T
        The instance of the desired trait type
    """
    return character.get_component(trait_type)


def remove_trait(character: GameObject, trait_type: Type[TraitComponent]) -> None:
    """Remove a trait from a character

    Parameters
    ----------
    character: GameObject
        The character to remove the trait from
    trait_type: Type[TraitComponent]
        The type of trait to remove
    """
    character.get_component(TraitManager).remove(trait_type)
    character.remove_component(trait_type)


def has_trait(character: GameObject, trait_type: Type[TraitComponent]) -> bool:
    """Check if a character has a trait

    Parameters
    ----------
    character: GameObject
        The character to check
    trait_type: Type[TraitComponent]
        The trait type to check for

    Returns
    -------
    bool
        True if the character has the given trait type
    """
    return character.has_component(trait_type)
