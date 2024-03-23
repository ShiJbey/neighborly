"""Location Preference System.

This module contains classes and functions that help characters decide where within the
settlement they spend most of their time. Since the simulation does not model
characters' positions throughout the settlement, this is a way of tracking who
characters have the highest likelihood of interacting with during a time step.

"""

import attrs
from sqlalchemy.orm import Mapped

# from neighborly.components.character import Character
from neighborly.ecs import Component, GameObject


class Location(Component):
    """Tracks the characters that frequent a location."""

    __tablename__ = "locations"

    is_private: Mapped[bool]
    """Private locations are not available to frequent except by certain characters."""
    # frequented_by: Mapped[list[Character]] = relationship()
    # """GameObject IDs of characters that frequent the location."""


class FrequentedLocations(Component):
    """Tracks the locations that a character frequents."""

    __tablename__ = "frequented_locations"

    # locations: Mapped[list[Location]]
    # """A set of GameObject IDs of locations."""


@attrs.define
class LocationPreferenceRule:
    """A rule that helps characters score how they feel about locations to frequent."""

    preconditions: list[str]
    """Precondition statements to run when scoring a location."""
    score: float
    """The amount to apply to the score."""

    def check_preconditions(self, obj: GameObject) -> float:
        """Check all preconditions and return a weight modifier.

        Parameters
        ----------
        gameobject
            A location to score.

        Returns
        -------
        float
            A probability score from [0.0, 1.0] of the character frequenting the
            location. Or -1 if it does not pass the preconditions.
        """

        raise NotImplementedError()
