from neighborly.components.activity import Activities


def test_activities_contains() -> None:
    activity_manager = Activities(
        {
            "Running",
            "Eating",
            "Drinking",
        }
    )

    assert "drinking" in activity_manager
    assert "Shopping" not in activity_manager
