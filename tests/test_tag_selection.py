"""Test the dynamic tag selection.

"""

from neighborly.helpers.content_selection import get_with_tags


def test_get_with_required_tags() -> None:
    """Test required tag selection."""

    results = get_with_tags(
        [("cat", ("animal",)), ("chicken", ("food", "animal")), ("pizza", ("food",))],
        ["food"],
    )

    assert "chicken" in results
    assert "pizza" in results


def test_get_with_optional_tags() -> None:
    """Test optional tag selection."""

    results = get_with_tags(
        [("cat", ("animal",)), ("chicken", ("food", "animal")), ("pizza", ("food",))],
        ["food", "~animal"],
    )

    assert "chicken" in results
    assert "pizza" not in results
