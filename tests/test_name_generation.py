import neighborly.core.name_generation as name_generator


def test_name_generation() -> None:
    name_generator.register_rule("first_name", ["John", "Calvin", "Sarah", "Caleb"])
    name_generator.register_rule(
        "last_name", ["Pizza", "Apple", "Blueberry", "Avocado"]
    )

    assert type(name_generator.get_name("#first_name# #family_name#")) == str
