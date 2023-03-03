from typing import Any, Dict, Optional, Protocol

from neighborly.core.action import Action
from neighborly.core.ecs import Component, GameObject, World


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
        Action
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
        super(Component, self).__init__()
        self.module: ISocialAIModule = module

    def get_next_action(self, world: World) -> Optional[Action]:
        """
        Calls the internal module to determine what action the character should take
        """
        return self.module.get_next_action(world, self.gameobject)

    def to_dict(self) -> Dict[str, Any]:
        return {}
