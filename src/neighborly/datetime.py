"""Simulation date representation.

Implements a 12 month calendar

"""

from __future__ import annotations

import copy
from typing import Any

MONTHS_PER_YEAR = 12
"""The number of months per calendar year."""


class SimDate:
    """Records the current date of the simulation counting in 1-month increments."""

    __slots__ = "_month", "_year", "_total_months"

    _month: int
    """The current month"""

    _year: int
    """The current year"""

    _total_months: int
    """Total number of elapsed months"""

    def __init__(self, year: int = 1, month: int = 1) -> None:
        """
        Parameters
        ----------
        month
            The month of the year [1, 12], default 1
        year
            The current year >= 1, default 1
        """
        if 1 <= month <= MONTHS_PER_YEAR:
            self._month = month - 1
        else:
            raise ValueError(
                f"Parameter 'month' must be between 1 and {MONTHS_PER_YEAR}"
            )

        if year >= 1:
            self._year = year - 1
        else:
            raise ValueError("Parameter 'year' must be greater than or equal to 1.")

        self._total_months = self._month + (self._year * MONTHS_PER_YEAR)

    @property
    def month(self) -> int:
        """The current month of the year [1 - 12]."""
        return self._month + 1

    @property
    def year(self) -> int:
        """The current year."""
        return self._year + 1

    @property
    def total_months(self) -> int:
        """Get the total number of elapsed months since month 1, year 1."""
        return self._total_months

    def increment_month(self) -> None:
        """Increments the month by one."""
        self._month += 1
        self._total_months += 1

        if self._month == MONTHS_PER_YEAR:
            self._month = 0
            self._year += 1

    def increment(self, months: int = 0, years: int = 0) -> None:
        """Increment the date by the given time."""
        carry_years, current_month = divmod(self._month + months, MONTHS_PER_YEAR)
        self._month = current_month
        self._total_months += months + (MONTHS_PER_YEAR * years)
        self._year += carry_years + years

    def to_iso_str(self) -> str:
        """Create an ISO date string of format YYYY-MM.

        Returns
        -------
        str
            The date string.
        """
        return f"{self.year:04d}-{self.month:02d}"

    def copy(self) -> SimDate:
        """Create a copy of this date."""
        return copy.copy(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(month={self.month}, year={self.year})"

    def __copy__(self) -> SimDate:
        return SimDate(month=self.month, year=self.year)

    def __deepcopy__(self, memo: dict[str, Any]) -> SimDate:
        return SimDate(month=self.month, year=self.year)

    def __str__(self) -> str:
        return self.to_iso_str()

    def __le__(self, other: SimDate) -> bool:
        return self.total_months <= other.total_months

    def __lt__(self, other: SimDate) -> bool:
        return self.total_months < other.total_months

    def __ge__(self, other: SimDate) -> bool:
        return self.total_months >= other.total_months

    def __gt__(self, other: SimDate) -> bool:
        return self.total_months > other.total_months

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimDate):
            raise TypeError(f"expected {type(self)} object but was {type(other)}")
        return self.total_months == other.total_months
