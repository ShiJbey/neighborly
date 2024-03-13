"""Neighborly Definition Compiler.

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

from typing import Any, Iterable, Type, TypeVar

from neighborly.defs.base_types import ContentDefinition

_T = TypeVar("_T", bound=ContentDefinition)


def compile_definitions(
    definition_type: Type[_T],
    definitions: Iterable[_T],
) -> list[_T]:
    """Compile final definitions from a collection of raw definitions."""

    unprocessed_defs: dict[str, _T] = {d.definition_id: d for d in definitions}
    processed_defs: dict[str, _T] = {}

    for definition in definitions:

        if definition.definition_id in processed_defs:
            # This one was already processed while processing another.
            continue

        _process_definition(
            definition_type, definition, unprocessed_defs, processed_defs
        )

    final_results: list[_T] = []

    for definition in processed_defs.values():
        definition.extends.clear()
        definition.variants.clear()
        final_results.append(definition)

    return final_results


def _process_definition(
    definition_type: Type[_T],
    definition: _T,
    unprocessed_defs: dict[str, _T],
    processed_defs: dict[str, _T],
) -> None:
    """Compile a single definition."""
    # We have to do the following to ensure that 'is_template' has the 'set' flag
    # and is not excluded from model_dump(...)
    if definition.is_template is False:
        definition.is_template = False

    # Variables to hold cumulative definition data
    final_definition_data: dict[str, Any] = {}
    final_definition_tags: set[str] = set()

    # Update the final definition data with all the parents data
    for parent_def_id in definition.extends:
        if parent_def_id not in processed_defs:
            _process_definition(
                definition_type,
                unprocessed_defs[parent_def_id],
                unprocessed_defs,
                processed_defs,
            )

        parent_def = processed_defs[parent_def_id]

        # Update cumulative variables with parent data
        final_definition_data.update(parent_def.model_dump(exclude_unset=True))
        final_definition_tags = final_definition_tags.union(parent_def.tags)

    # Lastly update cumulative variables with the current definition's data
    final_definition_data.update(definition.model_dump(exclude_unset=True))
    final_definition_data["tags"] = final_definition_tags.union(definition.tags)

    # This definition has been processed.
    final_definition = definition_type.model_validate(final_definition_data)
    processed_defs[final_definition.definition_id] = final_definition

    # Process any variants
    for variant_def in final_definition.variants:
        # We have to do the following to ensure that 'is_template' has the
        # 'set' flag and is not excluded from model_dump(...)
        if "name" not in variant_def:
            raise ValueError(
                f"{final_definition.definition_id} has variant that is missing a name."
            )

        variant_name = variant_def["name"]
        variant_tags: set[str] = set(variant_def.get("tags", []))

        variant_definition_data: dict[str, Any] = {}

        variant_definition_data.update(final_definition.model_dump(exclude_unset=True))

        variant_definition_data.update(variant_def)

        variant_id = f"{final_definition.definition_id}.{variant_name}"
        variant_definition_data["definition_id"] = variant_id
        variant_definition_data["tags"] = final_definition.tags.union(variant_tags)

        processed_defs[variant_id] = definition_type.model_validate(
            variant_definition_data
        )
