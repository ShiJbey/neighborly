"""Helper functions for managing residences and residents.

"""

from __future__ import annotations

from neighborly.defs.base_types import ResidenceDef
from neighborly.ecs import GameObject, World
from neighborly.libraries import ResidenceLibrary


def create_residence(
    world: World, district: GameObject, definition_id: str
) -> GameObject:
    """Create a new residence instance."""
    library = world.resources.get_resource(ResidenceLibrary)

    residence_def = library.get_definition(definition_id)

    residence = world.gameobjects.spawn_gameobject()
    residence.metadata["definition_id"] = definition_id

    residence_def.initialize(district, residence)

    return residence


def register_residence_def(world: World, definition: ResidenceDef) -> None:
    """Add a new residence definition for the ResidenceLibrary.

    Parameters
    ----------
    world
        The world instance containing the residence library.
    definition
        The definition to add.
    """
    world.resources.get_resource(ResidenceLibrary).add_definition(definition)


def change_residence():
    character = self.roles["subject"]
        new_residence = self.roles.get_first_or_none("new_residence")

        if resident := character.try_component(Resident):
            # This character is currently a resident at another location
            former_residence = resident.residence
            former_residence_comp = former_residence.get_component(ResidentialUnit)

            for resident in former_residence_comp.residents:
                if resident == character:
                    continue

                remove_trait(get_relationship(character, resident), "live_together")
                remove_trait(get_relationship(resident, character), "live_together")

            if former_residence_comp.is_owner(character):
                former_residence_comp.remove_owner(character)

            former_residence_comp.remove_resident(character)
            character.remove_component(Resident)

            former_district = former_residence.get_component(
                ResidentialUnit
            ).district.get_component(District)
            former_district.population -= 1

            if len(former_residence_comp) <= 0:
                former_residence.add_component(Vacant())

        # Don't add them to a new residence if none is given
        if new_residence is None:
            return

        # Move into new residence
        new_residence.get_component(ResidentialUnit).add_resident(character)

        if self.data["is_owner"]:
            new_residence.get_component(ResidentialUnit).add_owner(character)

        character.add_component(Resident(residence=new_residence))

        if new_residence.has_component(Vacant):
            new_residence.remove_component(Vacant)

        for resident in new_residence.get_component(ResidentialUnit).residents:
            if resident == character:
                continue

            add_trait(get_relationship(character, resident), "live_together")
            add_trait(get_relationship(resident, character), "live_together")

        new_district = new_residence.get_component(
            ResidentialUnit
        ).district.get_component(District)
        new_district.population += 1
