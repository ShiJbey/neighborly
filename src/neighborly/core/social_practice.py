from dataclasses import dataclass
from typing import Any, Callable, List, Dict

import esper

from neighborly.core.behavior_tree import BehaviorTree


SocialPracticePrecondition = Callable[
    [esper.World, Dict[str, List[int]], Dict[str, Any]], bool
]


@dataclass(frozen=True)
class SocialPracticeConfig:
    """Configuration parameters for social practices

    Attributes
    ----------
    name: str
        Name of the social practice
    description: str
        Description of the social practice
    preconditions: List[Callable[..., bool]]
        Functions that must evaluate to True for a
        practice to activate
    behaviors: Dict[str, List[str]]
        Names of CharacterBehaviors that are associated
        with the various roles in this practice
    update_fn:  Callable[[Dict[str, Any]], bool]
        Function used to update the state of the practice
    """

    name: str
    description: str
    preconditions: List[SocialPracticePrecondition]
    behaviors: Dict[str, List[str]]
    update_fn: Callable[[Dict[str, List[int]], Dict[str, Any]], bool]


_registered_social_practices: Dict[str, SocialPracticeConfig] = {}


def register_social_practice(practice_config: SocialPracticeConfig) -> None:
    """Register a social practice for use during simulation"""
    global _registered_social_practices
    _registered_social_practices[practice_config.name] = practice_config

def get_practice_config(name: str) -> SocialPracticeConfig:
    return _registered_social_practices[name]

class SocialPractice:
    """Collections of character behaviors organized by role

    Social Practices can have one or more participants, each
    with a given role within the social practice.
    (e.g. marriage, dating, workplace)

    Social Practices may be used as flags to check if a
    character has reached a certain status in their life.
    (e.g. adulthood or childhood)

    Attributes
    ----------
    config: SocialPracticeConfig
        Configuration settings for this instance of social practice
    roles: Dict[str, List[int]]
        Names of roles in this social practice mapped to characters
        that have that role
    metadata: Dict[str, Any]
        Additional data associated with this practice instance
    """

    __slots__ = "config", "roles", "metadata"

    def __init__(self, name: str, roles: Dict[str, List[int]], **kwargs) -> None:
        try:
            self.config = _registered_social_practices[name]
        except KeyError:
            raise ValueError(f"Could not find social practice with name: '{name}'")
        self.roles: Dict[str, List[int]] = roles
        self.metadata: Dict[str, Any] = {**kwargs}


@dataclass(frozen=True)
class CharacterBehavior:
    """
    Configuration information about a character behavior

    name: str
        Name of the behavior
    preconditions: List[Callable[..., bool]]
        Functions that need to return True for the behavior to run
    behavior_tree: BehaviorTree
        Behavior functionality
    """

    name: str
    preconditions: List[Callable[..., bool]]
    behavior_tree: BehaviorTree


_behavior_registry: Dict[str, CharacterBehavior] = {}


def register_character_behavior(behavior: CharacterBehavior) -> None:
    """Register the given behavior with the given name"""
    global _behavior_registry
    _behavior_registry[behavior.name] = behavior


class SocialPracticeManager:
    """Updates all its instances of social practices"""

    def __init__(self) -> None:
        self._active_practices: List[SocialPractice] = []

    def add_practice(self, practice: SocialPractice) -> None:
        self._active_practices.append(practice)

    def update(self) -> None:
        for practice in self._active_practices:
            practice.config.update_fn(practice.roles, practice.metadata)
