from abc import abstractmethod
from typing import Any, Dict, Optional, Protocol

from neighborly.core.ecs import Component, GameObject, World


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

    This is a wrapper class that tricks the ECS into thinking that all
    AI modules are the same, if you subclass this class, it will not be
    updated by default in the ECS, and will require its own system definition

    Attributes
    ----------
    module: IMovementAIModule
        AI module responsible for movement decision-making
    """

    __slots__ = "module"

    def __init__(self, module: IMovementAIModule) -> None:
        super(Component, self).__init__()
        self.module: IMovementAIModule = module

    def get_next_location(self, world: World) -> Optional[int]:
        """
        Calls the internal module to determine where the character should move
        """
        return self.module.get_next_location(world, self.gameobject)

    def to_dict(self) -> Dict[str, Any]:
        return {}
