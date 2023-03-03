"""
This module contains interfaces, components, and systems
related to character decision-making. Users of this library
should use these classes to override character decision-making
processes
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from neighborly.core.action import Action
from neighborly.core.ecs import Component, GameObject, World


class IAIBrain(ABC):
    """
    Interface defines functions that a class needs to implement to be
    injected into a MovementAI component.
    """

    @abstractmethod
    def get_type(self) -> str:
        """Return this brain type"""
        raise NotImplementedError

    @abstractmethod
    def get_next_location(self, world: World, gameobject: GameObject) -> Optional[int]:
        """
        Returns where the character will move to this simulation tick.

        Parameters
        ----------
        world: World
            The world that the character belongs to
        gameobject: GameObject
            The GameObject instance the module is associated with

        Returns
        -------
            The ID of the location to move to next
        """
        raise NotImplementedError

    @abstractmethod
    def execute_action(self, world: World, gameobject: GameObject) -> None:
        """
        Get the next action for this character

        Parameters
        ----------
        world: World
            The world instance the character belongs to
        gameobject: GameObject
            The GameObject instance this module is associated with
        """
        raise NotImplementedError

    @abstractmethod
    def append_action(self, action: Action) -> None:
        """Add an action to the internal queue"""
        raise NotImplementedError


class AIComponent(Component, IAIBrain):
    """
    Component responsible for moving a character around the simulation. It
    uses an IMovementAIModule instance to determine where the character
    should go.

    This is a wrapper class that tricks the ECS into thinking that all
    AI modules are the same, if you subclass this class, it will not be
    updated by default in the ECS, and will require its own system definition

    Attributes
    ----------
    brain: IAIBrain
        An AI brain responsible for movement decision-making
    """

    __slots__ = "brain"

    def __init__(self, brain: IAIBrain) -> None:
        super().__init__()
        self.brain: IAIBrain = brain

    def get_type(self) -> str:
        return self.brain.get_type()

    def get_next_location(self, world: World, gameobject: GameObject) -> Optional[int]:
        """
        Returns where the character will move to this simulation tick.

        Parameters
        ----------
        world: World
            The world that the character belongs to
        gameobject: GameObject
            The GameObject instance the module is associated with

        Returns
        -------
            The ID of the location to move to next
        """
        return self.brain.get_next_location(world, gameobject)

    def execute_action(self, world: World, gameobject: GameObject) -> None:
        """
        Get the next action for this character

        Parameters
        ----------
        world: World
            The world instance the character belongs to
        gameobject: GameObject
            The GameObject instance this module is associated with
        """
        self.brain.execute_action(world, gameobject)

    def append_action(self, action: Action) -> None:
        """Add an action to the internal queue"""
        self.brain.append_action(action)

    def to_dict(self) -> Dict[str, Any]:
        return {"brain_type": self.brain.get_type()}
