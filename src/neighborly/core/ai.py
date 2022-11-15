"""
This module contains interfaces, components, and systems
related to character decision-making. Users of this library
should use these classes to override character decision-making
processes
"""
from abc import abstractmethod
from typing import Optional, Protocol

from neighborly.builtin import helpers
from neighborly.builtin.components import Active
from neighborly.core.action import Action
from neighborly.core.ecs import Component, World, GameObject
from neighborly.core.system import System


class IMovementAIModule(Protocol):
    """
    Interface defines functions that a class needs to implement to be
    injected into a MovementAI component.
    """

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


class MovementAI(Component):
    """
    Component responsible for moving a character around the simulation. It
    uses an IMovementAIModule instance to determine where the character
    should go.

    Attributes
    ----------
    module: IMovementAIModule
        AI module responsible for movement decision-making
    """

    __slots__ = "module"

    def __init__(self, module: IMovementAIModule) -> None:
        super().__init__()
        self.module: IMovementAIModule = module

    def get_next_location(self, world: World) -> Optional[int]:
        """
        Calls the internal module to determine where the character should move
        """
        return self.module.get_next_location(world, self.gameobject)


class MovementAISystem(System):
    """Updates the MovementAI components attached to characters"""

    def run(self, *args, **kwargs) -> None:
        for gid, (movement_ai, _) in self.world.get_components(MovementAI, Active):
            next_location = movement_ai.get_next_location(self.world)
            if next_location is not None:
                helpers.move_to_location(
                    self.world, self.world.get_gameobject(gid), next_location
                )


class ISocialAIModule(Protocol):
    """
    Interface that defines how characters make decisions
    regarding social actions that they take between each other
    """

    def get_next_action(self, world: World, gameobject: GameObject) -> Optional[Action]:
        """
        Get the next action for this character

        Parameters
        ----------
        world: World
            The world instance the character belongs to
        gameobject: GameObject
            The GameObject instance this module is associated with

        Returns
        -------
            An instance of an action to take
        """
        raise NotImplementedError


class SocialAI(Component):
    """
    Component responsible for helping characters decide who to
    interact with and how.

    This class should not be subclassed as the subclasses will not
    be automatically recognized by Neighborly's default systems. If
    a subclass is necessary, then a new system will need to also be
    created to handle AI updates.

    Attributes
    ----------
    module: ISocialAIModule
        AI module responsible for social action decision-making
    """

    __slots__ = "module"

    def __init__(self, module: ISocialAIModule) -> None:
        super().__init__()
        self.module: ISocialAIModule = module

    def get_next_action(self, world: World) -> Optional[Action]:
        """
        Calls the internal module to determine what action the character should take
        """
        return self.module.get_next_action(world, self.gameobject)


class SocialAISystem(System):
    """Characters performs social actions"""

    def run(self, *args, **kwargs) -> None:
        for gid, (social_ai, _) in self.world.get_components(SocialAI, Active):
            next_action = social_ai.get_next_action(self.world)
            if next_action is not None:
                # TODO: Implement Action API
                pass
