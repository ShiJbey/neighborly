from dataclasses import dataclass, field
from heapq import heappush
from typing import Generic, TypeVar, Union, List, Tuple

_T = TypeVar("_T")


def clamp(
    value: Union[float, int], minimum: Union[float, int], maximum: Union[float, int]
) -> Union[float, int]:
    """
    Clamp numerical value between a [min, max] interval

    Parameters
    ----------
    value : Union[float, int]
        Value to clamp
    minimum : Union[float, int]
        Minimum value to return
    maximum : Union[float, int]
        Maximum value that can be returned

    Returns
    -------
    Union[float, int]
    """
    return max(minimum, min(value, maximum))


def choose_from_scored_options(options: List[Tuple[_T, float]]) -> _T:
    """Probabilistically chose one item from a list using their scores as weights"""
    items, scores = tuple(zip(*options))
    chosen_item: _T = random.choices(items, weights=scores, k=1)[0]  # type: ignore
    return chosen_item


def int_to_roman(num: int) -> str:
    """Convert a given int to a Roman numeral string"""
    # From https://www.w3resource.com/python-exercises/class-exercises/python-class-exercise-1.php
    lookup = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    res = ""
    for (n, roman) in lookup:
        (d, num) = divmod(num, n)
        res += roman * d
    return res


def roman_to_int(roman: str) -> int:
    """Convert Roman numeral string to int"""
    roman_lookup = {
        "I": 1,
        "IV": 4,
        "V": 5,
        "IX": 9,
        "X": 10,
        "XL": 40,
        "L": 50,
        "XC": 90,
        "C": 100,
        "CD": 400,
        "D": 500,
        "CM": 900,
        "M": 1000,
    }

    i = 0
    num = 0
    while i < len(roman):
        if i + 1 < len(roman) and roman[i: i + 2] in roman_lookup:
            num += roman_lookup[roman[i: i + 2]]
            i += 2
        else:
            # print(i)
            num += roman_lookup[roman[i]]
            i += 1
    return num


def int_to_ordinal(num: int) -> str:
    """
    Returns ordinal number string from int, e.g. 1, 2, 3 becomes 1st, 2nd, 3rd, etc.
    """
    n = int(num)
    if 4 <= n <= 20:
        return f"{n}th"
    elif n == 1 or (n % 10) == 1:
        return f"{n}st"
    elif n == 2 or (n % 10) == 2:
        return f"{n}nd"
    elif n == 3 or (n % 10) == 3:
        return f"{n}rd"
    elif n < 100:
        return f"{n}th"
    return f"{n}th"


@dataclass(order=True)
class PrioritizedItem(Generic[_T]):
    priority: float
    item: _T = field(compare=False)


class PriorityQueue(Generic[_T]):
    def __init__(self) -> None:
        self._queue: List[PrioritizedItem[_T]] = []

    def push(self, priority: float, item: _T) -> None:
        heappush(self._queue, PrioritizedItem[_T](priority, item))

    def pop(self) -> _T:
        return self._queue.pop(0).item

    def __repr__(self) -> str:
        return self._queue.__repr__()
