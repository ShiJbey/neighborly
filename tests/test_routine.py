from typing import Dict, List

from neighborly.core.ai.brain import GoalNode
from neighborly.core.ecs import GameObject


class _GoToWork(GoalNode):
    def is_complete(self) -> bool:
        return super().is_complete()

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()

    def satisfied_goals(self) -> List[GoalNode]:
        return super().satisfied_goals()

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, _GoToWork)


class _GoHome(GoalNode):
    def is_complete(self) -> bool:
        return super().is_complete()

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()

    def satisfied_goals(self) -> List[GoalNode]:
        return super().satisfied_goals()

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, _GoHome)


class _RunErrands(GoalNode):
    def is_complete(self) -> bool:
        return super().is_complete()

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()

    def satisfied_goals(self) -> List[GoalNode]:
        return super().satisfied_goals()

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, _RunErrands)
