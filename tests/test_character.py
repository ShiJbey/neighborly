from typing import Any, Dict

import pytest
import yaml

from neighborly.core.character import CharacterDefinition


@pytest.fixture()
def sample_definitions() -> str:
    return """
        CharacterDefinitions:
          -
            name: BaseCharacter
            generation:
                first_name: "#first_name#"
                last_name: "#family_name#"
                family:
                    probability_spouse: 0.5
                    probability_children: 0.5
                    num_children: "0-2"
            lifecycle:
                can_age: yes
                can_die: yes
                chance_of_death: 0.8
                romantic_feelings_age: 13
                marriageable_age: 18
                age_ranges:
                    child: "0-12"
                    adolescent: "13-19"
                    young_adult: "20-29"
                    adult: "30-65"
                    senior: "65-100"
        """


def test_merge_definitions(sample_definitions: str):
    """Test that CharacterDefinitions can inherit from a parent"""
    assert True


def test_parse_character_definition(sample_definitions: str):
    """Test that character definitions are properly parsed"""
    data: Dict[str, Any] = yaml.safe_load(sample_definitions)

    assert "CharacterDefinitions" in data

    base_character_def_data = data["CharacterDefinitions"][0]

    assert "BaseCharacter" == base_character_def_data["name"]

    base_character_def = CharacterDefinition(**base_character_def_data)

    assert "BaseCharacter" == base_character_def.name
