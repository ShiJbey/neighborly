"""Neighborly Yaml Compiler  Tests.

This script contains a best attempt at recreating the YAML configuration file workflow
described by Patrick Kemp @ Spry Fox Games.

It is based on this talk:
https://www.youtube.com/watch?v=rWPJ5fW1UH8&t=538s

This script aims to reproduce the following capabilities:

1) Allow character definitions to include other character definitions as boilerplate
   data
2) Enable users to specify definition variants that expand to final definitions
3) Support additive tags. So a definition's tag set is a combination of its defined
   tags and the tags of any parent definitions.

"""

from typing import Any

from neighborly.definition_compiler import compile_definitions
from neighborly.defs.business import DefaultBusinessDef
from neighborly.defs.character import DefaultCharacterDef


def test_compiler():
    """Test the definition compiler."""

    definition_data: list[dict[str, Any]] = [
        {
            "definition_id": "person",
            "species": "human",
            "is_template": True,
            "stats": [
                {"stat": "confidence"},
                {"stat": "intelligence"},
                {"stat": "reliability"},
                {"stat": "attractiveness"},
                {"stat": "sociability"},
                {"stat": "stewardship"},
                {"stat": "fertility"},
                {"stat": "boldness"},
            ],
            "tags": ["person"],
            "variants": [
                {
                    "definition_id": "male",
                    "first_name_factory": "masculine_names",
                    "last_name_factory": "last_names",
                    "sex": "male",
                    "tags": ["male"],
                },
                {
                    "definition_id": "female",
                    "first_name_factory": "feminine_names",
                    "last_name_factory": "last_names",
                    "sex": "female",
                    "tags": ["female"],
                },
            ],
        },
        {
            "definition_id": "farmer",
            "is_template": True,
            "extends": ["person"],
            "skills": [{"with_id": "farming", "value_range": "50 - 150"}],
            "tags": ["farmer"],
        },
    ]

    input_definitions = [DefaultCharacterDef.model_validate(d) for d in definition_data]

    results = {d.definition_id: d for d in compile_definitions(input_definitions)}

    assert "farmer.male" in results
    assert "farmer.female" in results
    assert "farmer.female" in results

    definition_data: list[dict[str, Any]] = [
        {
            "definition_id": "cafe",
            "name": "Cafe",
            "spawn_frequency": 1,
            "owner_role": "cafe_owner",
            "employee_roles": {"barista": 2},
            "tags": ["cafe"],
        },
        {
            "definition_id": "farm",
            "name": "Farm",
            "spawn_frequency": 1,
            "owner_role": "farmer",
            "employee_roles": {"farmhand": 2},
            "tags": ["farm"],
        },
    ]

    input_definitions = [DefaultBusinessDef.model_validate(d) for d in definition_data]

    results = {d.definition_id for d in compile_definitions(input_definitions)}

    assert "cafe" in results
    assert "farm" in results
