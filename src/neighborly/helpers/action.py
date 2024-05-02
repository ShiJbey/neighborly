"""Action System Helper Functions.

"""

from neighborly.action import Action
from neighborly.libraries import ActionConsiderationLibrary


def get_action_utility(action: Action) -> float:
    """Calculate the utility of a given action."""

    consideration_library = action.world.resources.get_resource(
        ActionConsiderationLibrary
    )

    considerations = consideration_library.get_utility_considerations(
        action.action_id()
    )

    # We set the starting score to 1 since we are multiplying probabilities
    score: float = 1
    consideration_count: int = 0

    for consideration in considerations:

        utility_score = consideration(action)

        if utility_score < 0.0:
            continue

        elif utility_score == 0.0:
            return 0.0

        # Update the current score and counts
        score = score * utility_score
        consideration_count += 1

    if consideration_count == 0:
        return 0.5
    else:
        return score ** (1 / consideration_count)


def get_action_success_probability(action: Action) -> float:
    """Calculate the probability of a given action being successful."""

    consideration_library = action.world.resources.get_resource(
        ActionConsiderationLibrary
    )

    considerations = consideration_library.get_success_considerations(
        action.action_id()
    )

    # We set the starting score to 1 since we are multiplying probabilities
    score: float = 1
    consideration_count: int = 0

    for consideration in considerations:

        utility_score = consideration(action)

        if utility_score < 0.0:
            continue

        elif utility_score == 0.0:
            return 0.0

        # Update the current score and counts
        score = score * utility_score
        consideration_count += 1

    if consideration_count == 0:
        return 0.5
    else:
        return score ** (1 / consideration_count)
