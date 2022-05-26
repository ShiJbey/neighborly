from typing import Dict, Tuple, Generator, TypeVar


def merge(source: Dict, destination: Dict) -> Dict:
    """
    Deep merge two dictionaries

    Parameters
    ----------
    source: Dict[Any, Any]
        Dictionary to merge from
    destination: Dict[Any, Any]
        Dictionary to merge to

    Returns
    -------
    Dict[Any, Any]
        New dictionary with fields in destination overwritten
        with values from source
    """
    new_dict = {**destination}

    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = new_dict.get(key, {})
            new_dict[key] = merge(value, node)
        else:
            new_dict[key] = value

    return new_dict


def parse_number_range(range_str: str) -> Tuple[int, int]:
    """
    Parse number range of non-negative integers given as a range string (i.e. "0-3", "5-13", ...)

    Parameters
    ----------
    range_str:
        A range string (i.e. "0-3", "5-13", ...)

    Returns
    -------
    Tuple[int, int]
    """
    range_min, range_max = tuple(
        map(lambda s: int(s.strip()), range_str.strip().split("-"))
    )
    return range_min, range_max


_T = TypeVar("_T")


def chunk_list(lst: list[_T], n: int) -> Generator[list[_T], None, None]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
