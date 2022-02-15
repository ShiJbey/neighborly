from neighborly.core.character.character import GameCharacter
from neighborly.core.ecs import World
from neighborly.core.social_practice import CharacterBehavior
from neighborly.ai.behavior_tree import AbstractBTNode, NodeState, Blackboard
from neighborly.ai import behavior_utils


class DieAction(AbstractBTNode):
    def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
        world: World = blackboard.get_value('world')
        character_id: int = blackboard.get_value('self')
        character = world.get_gameobject(character_id).get_component(GameCharacter)

        return NodeState.SUCCESS


_die_behavior = CharacterBehavior(
    name="die",
    preconditions=[lambda world, character_id: behavior_utils.can_die(world, character)]
    behavior_tree=
)
