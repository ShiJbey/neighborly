"""Content selection helper functions.

"""

from typing import Iterable, TypeVar

_T = TypeVar("_T")


def get_with_tags(
    options: list[tuple[_T, Iterable[str]]], tags: Iterable[str]
) -> list[_T]:
    """Get a definition from the library with the given tags.

    Parameters
    ----------
    options
        Tuples of items with their tags.
    tags
        A collection of mandatory and optional tags.

    Returns
    -------
    List[_T]
        The items in options that best match the tags.
    """

    matches: list[tuple[_T, int]] = []

    mandatory_tags = set(t for t in tags if t[0] != "~")
    optional_tags = set(t[1:] for t in tags if t[0] == "~")

    for entry, entry_tags in options:
        entry_tag_set = set(entry_tags)
        unsatisfied_mandatory_tags = mandatory_tags.difference(entry_tag_set)
        mandatory_tags_present = len(unsatisfied_mandatory_tags) == 0

        satisfied_optional_tags = optional_tags.intersection(entry_tag_set)
        optional_tags_count = len(satisfied_optional_tags)

        if mandatory_tags_present:
            matches.append((entry, optional_tags_count))

    if matches:  # something exists
        matches.sort(key=lambda x: x[1], reverse=True)

        max_optional_tags_count = matches[0][1]

        best_matches = [
            definition
            for definition, optional_tags_count in matches
            if optional_tags_count == max_optional_tags_count
        ]

        return best_matches

    return []
