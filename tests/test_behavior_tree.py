# from typing import List, Optional

# from behavior_tree import AbstractBTNode, NodeState, SelectorBTNode, SequenceBTNode, Blackboard


# class GetEggs(AbstractBTNode):

#     def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
#         dietary_restriction: Optional[str] = blackboard.get_value(
#             "dietary_restriction", False)
#         if dietary_restriction == 'vegan':
#             self._state = NodeState.FAILURE
#         else:
#             action_queue: List[str] = blackboard.get_value("action_queue")
#             action_queue.append("Getting eggs")
#             self._state = NodeState.SUCCESS
#         return self._state


# class GetAppleSauce(AbstractBTNode):

#     def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
#         action_queue: List[str] = blackboard.get_value("action_queue")
#         action_queue.append("Getting apple sauce")
#         self._state = NodeState.SUCCESS
#         return self._state


# class MixIngredientAction(AbstractBTNode):

#     def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
#         action_queue: List[str] = blackboard.get_value("action_queue")
#         action_queue.append("Mixing Ingredients")
#         self._state = NodeState.SUCCESS
#         return self._state


# class HeatOvenAction(AbstractBTNode):

#     def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
#         action_queue: List[str] = blackboard.get_value("action_queue")
#         action_queue.append("Heating Oven")
#         self._state = NodeState.SUCCESS
#         return self._state


# class BakeAction(AbstractBTNode):

#     def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
#         action_queue: List[str] = blackboard.get_value("action_queue")
#         action_queue.append("Baking cake")
#         self._state = NodeState.SUCCESS
#         return self._state


# class EatAction(AbstractBTNode):

#     def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
#         action_queue: List[str] = blackboard.get_value("action_queue")
#         action_queue.append("Eating Cake")
#         self._state = NodeState.SUCCESS
#         return self._state


# def test_behavior_tree_sequence():
#     """Ensure nodes are executed in sequence"""

#     baking_tree = SequenceBTNode([
#         MixIngredientAction(),
#         HeatOvenAction(),
#         BakeAction(),
#         EatAction(),
#     ])

#     blackboard = Blackboard({
#         "action_queue": []
#     })

#     baking_tree.evaluate(blackboard)

#     expected = [
#         "Mixing Ingredients",
#         "Heating Oven",
#         "Baking cake",
#         "Eating Cake"
#     ]

#     action_queue: List[str] = blackboard.get_value("action_queue")

#     assert action_queue == expected


# def test_behavior_tree_selector():
#     baking_tree = SequenceBTNode([
#         SelectorBTNode([
#             GetEggs(),
#             GetAppleSauce(),
#         ]),
#         MixIngredientAction(),
#         HeatOvenAction(),
#         BakeAction(),
#         EatAction(),
#     ])

#     blackboard = Blackboard({
#         "action_queue": [],
#         "dietary_restriction": 'vegan'
#     })

#     res = baking_tree.evaluate(blackboard)

#     assert res == NodeState.SUCCESS

#     expected = [
#         "Getting apple sauce",
#         "Mixing Ingredients",
#         "Heating Oven",
#         "Baking cake",
#         "Eating Cake"
#     ]

#     action_queue: List[str] = blackboard.get_value("action_queue")

#     assert action_queue == expected
