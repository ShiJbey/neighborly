"""Built-in Systems.

This module contains built-in systems that help simulations function.

"""

from __future__ import annotations

from neighborly.components.business import JobRole
from neighborly.components.character import SpeciesType
from neighborly.components.relationship import (
    RelationshipModifier,
    RelationshipModifiers,
)
from neighborly.components.shared import Modifier, Modifiers
from neighborly.components.skills import Skill
from neighborly.components.traits import Trait, Traits
from neighborly.datetime import SimDate
from neighborly.definitions import compile_definitions
from neighborly.ecs import Active, System, World
from neighborly.helpers.traits import remove_trait
from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    EffectLibrary,
    JobRoleLibrary,
    PreconditionLibrary,
    SettlementLibrary,
    SkillLibrary,
    SpeciesLibrary,
    TraitLibrary,
)


class CompileTraitDefsSystem(System):
    """Instantiates all the trait definitions within the TraitLibrary."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        trait_library = world.resource_manager.get_resource(TraitLibrary)
        effect_library = world.resource_manager.get_resource(EffectLibrary)

        # Compile the loaded definitions
        compiled_defs = compile_definitions(trait_library.definitions.values())

        # Clear out the unprocessed ones
        trait_library.definitions.clear()

        # Add the new definitions and instances to the library.
        for trait_def in compiled_defs:
            if not trait_def.is_template:
                trait_library.add_definition(trait_def)

                trait = Trait(
                    definition_id=trait_def.definition_id,
                    name=trait_def.name,
                    inheritance_chance_both=trait_def.inheritance_chance_both,
                    inheritance_chance_single=trait_def.inheritance_chance_single,
                    is_inheritable=(
                        trait_def.inheritance_chance_single > 0
                        or trait_def.inheritance_chance_both > 0
                    ),
                    description=trait_def.description,
                    effects=[
                        effect_library.create_from_obj(
                            world, {"reason": f"Has {trait_def.name} trait", **entry}
                        )
                        for entry in trait_def.effects
                    ],
                    conflicting_traits=trait_def.conflicts_with,
                )

                trait_library.add_trait(trait)


class CompileSpeciesDefsSystem(System):
    """Instantiates all the species definitions within the SpeciesLibrary."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(SpeciesLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)

                min_lifespan, max_lifespan = tuple(
                    int(x.strip()) for x in definition.lifespan.split("-")
                )

                library.add_species(
                    SpeciesType(
                        definition_id=definition.definition_id,
                        name=definition.name,
                        description=definition.description,
                        adolescent_age=definition.adolescent_age,
                        young_adult_age=definition.young_adult_age,
                        adult_age=definition.adult_age,
                        senior_age=definition.senior_age,
                        lifespan=(min_lifespan, max_lifespan),
                        can_physically_age=definition.can_physically_age,
                        traits=[*definition.traits],
                        adolescent_female_fertility=definition.adolescent_female_fertility,
                        young_adult_female_fertility=definition.young_adult_female_fertility,
                        adult_female_fertility=definition.adult_female_fertility,
                        senior_female_fertility=definition.senior_female_fertility,
                        adolescent_male_fertility=definition.adolescent_male_fertility,
                        young_adult_male_fertility=definition.young_adult_male_fertility,
                        adult_male_fertility=definition.adult_male_fertility,
                        senior_male_fertility=definition.senior_male_fertility,
                        fertility_cost_per_child=definition.fertility_cost_per_child,
                    )
                )


class CompileSkillDefsSystem(System):
    """Instantiates all the skill definitions within the SkillLibrary."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        skill_library = world.resource_manager.get_resource(SkillLibrary)

        # Compile the loaded definitions
        compiled_defs = compile_definitions(skill_library.definitions.values())

        # Clear out the unprocessed ones
        skill_library.definitions.clear()

        # Add the new definitions and instances to the library.
        for skill_def in compiled_defs:
            if not skill_def.is_template:
                skill_library.add_definition(skill_def)

                skill_library.add_skill(
                    Skill(
                        definition_id=skill_def.definition_id,
                        name=skill_def.name,
                        description=skill_def.description,
                        tags=set(*skill_def.tags),
                    )
                )


class CompileJobRoleDefsSystem(System):
    """Instantiates all the job role definitions within the TraitLibrary."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        job_role_library = world.resource_manager.get_resource(JobRoleLibrary)
        effect_library = world.resource_manager.get_resource(EffectLibrary)
        precondition_library = world.resource_manager.get_resource(PreconditionLibrary)

        # Compile the loaded definitions
        compiled_defs = compile_definitions(job_role_library.definitions.values())

        # Clear out the unprocessed ones
        job_role_library.definitions.clear()

        # Add the new definitions and instances to the library.
        for role_def in compiled_defs:
            if not role_def.is_template:
                job_role_library.add_definition(role_def)

                job_role_library.add_role(
                    JobRole(
                        definition_id=role_def.definition_id,
                        name=role_def.name,
                        job_level=role_def.job_level,
                        description=role_def.description,
                        requirements=[
                            precondition_library.create_from_obj(world, entry)
                            for entry in role_def.requirements
                        ],
                        effects=[
                            effect_library.create_from_obj(world, entry)
                            for entry in role_def.effects
                        ],
                    )
                )


class CompileDistrictDefsSystem(System):
    """Compile district definitions."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(DistrictLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)


class CompileSettlementDefsSystem(System):
    """Compile settlement definitions."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(SettlementLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)


class CompileCharacterDefsSystem(System):
    """Compile character definitions."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(CharacterLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)


class CompileBusinessDefsSystem(System):
    """Compile business definitions."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        library = world.resource_manager.get_resource(BusinessLibrary)

        compiled_defs = compile_definitions(library.definitions.values())

        library.definitions.clear()

        for definition in compiled_defs:
            if not definition.is_template:
                library.add_definition(definition)


class TickModifiersSystem(System):
    """Tick all modifiers."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (modifier_manager, _) in world.get_components((Modifiers, Active)):
            modifiers_to_remove: list[Modifier] = []

            for modifier in modifier_manager.modifiers:
                if modifier.is_expired():
                    modifiers_to_remove.append(modifier)
                    continue
                else:
                    modifier.update(modifier_manager.gameobject)

            for modifier in modifiers_to_remove:
                modifier_manager.remove_modifier(modifier)

        for _, (modifier_manager, _) in world.get_components(
            (RelationshipModifiers, Active)
        ):
            rel_modifiers_to_remove: list[RelationshipModifier] = []

            for modifier in modifier_manager.modifiers:
                if modifier.is_expired():
                    rel_modifiers_to_remove.append(modifier)
                    continue
                else:
                    modifier.update(modifier_manager.gameobject)

            for modifier in rel_modifiers_to_remove:
                modifier_manager.remove_modifier(modifier)


class TickTraitsSystem(System):
    """Tick all trait durations."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (traits, _) in world.get_components((Traits, Active)):
            traits_to_remove: list[Trait] = []

            for trait_instance in traits.traits.values():
                if not trait_instance.has_duration:
                    continue

                trait_instance.duration -= 1

                if trait_instance.duration <= 0:
                    traits_to_remove.append(trait_instance.trait)

            for trait in traits_to_remove:
                remove_trait(traits.gameobject, trait.definition_id)


class TimeSystem(System):
    """Increments the current date/time."""

    __system_group__ = "LateUpdateSystems"
    __update_order__ = ("last",)

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)

        current_date.increment_month()
