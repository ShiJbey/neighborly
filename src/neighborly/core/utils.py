import random
from pathlib import Path
from typing import List, Optional, Union

AnyPath = Union[str, Path]


class DefaultNameGenerator:
    """
    Factory functions that, given a list of names or a file
    containing names returns a string at random for a name
    """

    __slots__ = "_names"

    def __init__(self, names_list: Optional[List[str]] = None, filepath: Optional[AnyPath] = None) -> None:
        if names_list and filepath:
            raise ValueError("Only supply names list or file path not both")
        if names_list:
            self._names: List[str] = [*names_list]
        elif filepath:
            with open(filepath, 'r') as f:
                self._names: List[str] = f.read().splitlines()
        else:
            raise ValueError("No YAML string or file path given")

    def __call__(self) -> str:
        return random.choice(self._names)
