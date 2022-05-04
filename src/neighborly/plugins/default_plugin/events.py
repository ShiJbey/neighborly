import logging
from typing import Optional

from neighborly.core.business import Business, Occupation, OccupationDefinition
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import EventLog, LifeEvent, LifeEventRecord
from neighborly.core.location import Location
from neighborly.core.relationship import RelationshipTag
from neighborly.core.residence import Residence
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import SimDateTime
from neighborly.plugins.default_plugin.statuses import (
    AdolescentStatus,
    AdultStatus,
    ChildStatus,
    DatingStatus,
    MarriedStatus,
    RetiredStatus,
    SeniorStatus,
    UnemployedStatus,
    YoungAdultStatus,
)

logger = logging.getLogger(__name__)


class DeathEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""
            character = gameobject.get_component(GameCharacter)
            return (
                character.alive
                and character.age
                > character.character_def.lifecycle.age_ranges["senior"][0]
            )

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            logger.debug(
                f"{str(character.name)} died at the age of {round(character.age)}"
            )

            character.alive = False

            if character.location:
                world.get_gameobject(character.location).get_component(
                    Location
                ).remove_character(character.gameobject.id)

            home_id = character.location_aliases.get("home")
            if home_id:
                world.get_gameobject(home_id).get_component(Residence).remove_tenant(
                    character.gameobject.id
                )

            world.get_resource(RelationshipNetwork).remove_node(character.gameobject.id)

            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )

            world.delete_gameobject(character.gameobject.id)

        # end callback

        super().__init__("Death", p, cb, 0.8)


class BecameChildEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            character = gameobject.get_component(GameCharacter)
            child_age_min, child_age_max = character.character_def.lifecycle.age_ranges[
                "child"
            ]
            return (
                character.alive
                and child_age_min <= character.age <= child_age_max
                and not gameobject.has_component(ChildStatus)
            )

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} became and child")
            gameobject.add_component(ChildStatus())
            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )

        # end callback

        super().__init__("Became Child", p, cb)


class BecameAdolescentEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            character = gameobject.get_component(GameCharacter)
            (
                adolescent_age_min,
                adolescent_age_max,
            ) = character.character_def.lifecycle.age_ranges["teen"]
            return (
                character.alive
                and adolescent_age_min <= character.age <= adolescent_age_max
                and not gameobject.has_component(AdolescentStatus)
            )

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} became and adolescent")
            gameobject.add_component(AdolescentStatus())
            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )

        # end callback

        super().__init__("Became Adolescent", p, cb)


class BecameYoungAdultEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            character = gameobject.get_component(GameCharacter)
            age_min, age_max = character.character_def.lifecycle.age_ranges[
                "young_adult"
            ]
            return (
                character.alive
                and age_min <= character.age <= age_max
                and not gameobject.has_component(YoungAdultStatus)
            )

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} became and young adult")
            gameobject.add_component(YoungAdultStatus())
            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )

        # end callback

        super().__init__("Became Young Adult", p, cb)


class BecameAdultEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            character = gameobject.get_component(GameCharacter)
            age_min, age_max = character.character_def.lifecycle.age_ranges["adult"]
            return (
                character.alive
                and age_min <= character.age <= age_max
                and not gameobject.has_component(AdultStatus)
            )

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} became and adult")
            character.gameobject.add_component(AdultStatus())
            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )

        # end callback

        super().__init__("Became Adult", p, cb)


class BecameSeniorEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            character = gameobject.get_component(GameCharacter)
            age_min, _ = character.character_def.lifecycle.age_ranges["senior"]
            return (
                character.alive
                and age_min <= character.age
                and not gameobject.has_component(SeniorStatus)
            )

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} became and senior")
            character.gameobject.add_component(SeniorStatus())
            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )

        # end callback

        super().__init__("Became Senior", p, cb)


class UnemploymentEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""

            return not gameobject.has_component(UnemployedStatus) and (
                gameobject.has_component(YoungAdultStatus)
                or gameobject.has_component(AdultStatus)
            )

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} became unemployed")
            gameobject.add_component(UnemployedStatus())
            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )

        # end callback

        super().__init__("Became Unemployed", p, cb)


class BecameBusinessOwnerEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Characters get hired if they are unemployed"""
            is_unemployed = gameobject.has_component(UnemployedStatus)

            # There is a business that needs an owner
            businesses_without_owners = list(
                filter(
                    lambda res: res[1].needs_owner(),
                    gameobject.world.get_component(Business),
                )
            )

            return is_unemployed and bool(businesses_without_owners)

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            """Remove the character from the world"""
            businesses_without_owners = list(
                filter(
                    lambda res: res[1].needs_owner(),
                    gameobject.world.get_component(Business),
                )
            )

            business_id, business = businesses_without_owners[0]

            owner_typename = business.get_type().owner_type

            if owner_typename is None:
                raise RuntimeError(
                    "Missing owner occupation type for business that needs owner"
                )

            occupation_type = OccupationDefinition.get_registered_type(owner_typename)

            gameobject.add_component(Occupation(occupation_type, business_id))

            character = gameobject.get_component(GameCharacter)

            business.hire_owner(character.gameobject.id)

            world = gameobject.world

            logger.debug(f"{str(character.name)} became owner of {business.get_name()}")

            gameobject.remove_component(gameobject.get_component(UnemployedStatus))

            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id], "business": business_id},
                ),
                [gameobject.id],
            )

        # end callback

        super().__init__("Became Business Owner", p, cb)


class GetHiredEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Characters get hired if they are unemployed"""
            is_unemployed = gameobject.has_component(UnemployedStatus)

            # There is a business with vacancies
            businesses = gameobject.world.get_component(Business)

            return is_unemployed

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} got hired")
            gameobject.remove_component(gameobject.get_component(UnemployedStatus))
            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )

        # end callback

        super().__init__("Get Hired", p, cb)


class StartedDatingEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""
            if gameobject.has_component(DatingStatus):
                return False

            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            relationship_net = world.get_resource(RelationshipNetwork)

            love_interests = relationship_net.get_all_relationships_with_tags(
                character.gameobject.id, RelationshipTag.LoveInterest
            )

            love_interests_that_know_you = [
                relationship_net.get_connection(r.target, character.gameobject.id)
                for r in love_interests
                if relationship_net.has_connection(r.target, character.gameobject.id)
            ]

            single_love_interests = [
                li
                for li in love_interests_that_know_you
                if not gameobject.world.get_gameobject(li.owner).has_component(
                    DatingStatus
                )
            ]

            return any(
                [r.has_tag(RelationshipTag.LoveInterest) for r in single_love_interests]
            )

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            relationship_net = world.get_resource(RelationshipNetwork)

            love_interests = relationship_net.get_all_relationships_with_tags(
                character.gameobject.id, RelationshipTag.LoveInterest
            )

            love_interests_that_know_you = list(
                filter(
                    lambda rel: rel.has_tag(RelationshipTag.LoveInterest),
                    [
                        relationship_net.get_connection(
                            r.target, character.gameobject.id
                        )
                        for r in love_interests
                        if relationship_net.has_connection(
                            r.target, character.gameobject.id
                        )
                    ],
                )
            )

            single_love_interests = [
                li
                for li in love_interests_that_know_you
                if not gameobject.has_component(DatingStatus)
            ]

            potential_mate: int = (
                world.get_resource(NeighborlyEngine)
                .get_rng()
                .choice(single_love_interests)
                .owner
            )

            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id, potential_mate]},
                ),
                [gameobject.id, potential_mate],
            )

            world.get_gameobject(potential_mate).add_component(
                DatingStatus(
                    gameobject.id, str(gameobject.get_component(GameCharacter).name)
                )
            )

            gameobject.add_component(
                DatingStatus(
                    potential_mate,
                    str(
                        world.get_gameobject(potential_mate)
                        .get_component(GameCharacter)
                        .name
                    ),
                )
            )

            logger.debug(
                f"{str(character.name)} and {str(world.get_gameobject(potential_mate).get_component(GameCharacter).name)} started dating"
            )

        # end callback

        super().__init__("Dating", p, cb)


class DatingBreakUpEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Break up with your partner if you're not one of their love interests"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            if not gameobject.has_component(DatingStatus):
                return False

            dating_status = gameobject.get_component(DatingStatus)

            partner_id: int = dating_status.partner_id

            relationship_net = world.get_resource(RelationshipNetwork)

            # rel = relationship_net.get_connection(partner_id, gameobject.id)
            #
            # if character.gameobject.id not in partner_love_interests:
            #     return True

            return False

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            """Remove the dating status"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            dating_status = gameobject.get_component(DatingStatus)

            partner_id: int = dating_status.partner_id
            partner_name: str = dating_status.partner_name

            partner = world.get_gameobject(partner_id)

            partner.remove_component(partner.get_component(DatingStatus))
            gameobject.remove_component(gameobject.get_component(DatingStatus))

            logger.debug(f"{str(character.name)} and {str(partner_name)} broke up")

            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id, partner_id]},
                ),
                [gameobject.id, partner_id],
            )

        # end callback

        super().__init__("Break Up", p, cb)


class MarriageEvent(LifeEvent):
    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""
            return gameobject.has_component(DatingStatus)

        # end precondition

        def cb(gameobject: GameObject, **kwargs) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            married_status = gameobject.get_component(DatingStatus)

            partner_id: int = married_status.partner_id
            partner_name: str = married_status.partner_name

            # Remove dating status from characters
            gameobject.remove_component(gameobject.get_component(DatingStatus))
            world.get_gameobject(partner_id).remove_component(
                gameobject.get_component(DatingStatus)
            )

            # Add Married status to characters
            gameobject.add_component(MarriedStatus(partner_id, partner_name))
            world.get_gameobject(partner_id).add_component(
                MarriedStatus(character.gameobject.id, str(character.name))
            )

            world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id, partner_id]},
                ),
                [gameobject.id, partner_id],
            )

            logger.debug(f"{str(character.name)} and {str(partner_name)} got married.")

        # end callback

        super().__init__("Marriage", p, cb)


class FindTheirOwnPlace(LifeEvent):
    """
    Character moves out of a home when they don't own
    as a young adult or adult with a job
    """

    def __init__(self, chance_move_out: float) -> None:
        def p(gameobject: GameObject) -> bool:
            character = gameobject.get_component(GameCharacter)
            current_residence = gameobject.world.get_gameobject(
                character.location_aliases["home"]
            ).get_component(Residence)

            is_home_owner = gameobject.id in current_residence.owners

            return (
                gameobject.has_component(Occupation)
                and (
                    gameobject.has_component(YoungAdultStatus)
                    or gameobject.has_component(AdultStatus)
                )
                and not is_home_owner
            )

        def cb(gameobject: GameObject, **kwargs) -> None:
            # Find a residence to move into
            residence: Optional[Residence] = try_find_housing(gameobject.world)
            if residence:
                # Move into the residence and take their nuclear family with them
                move_into_residence(gameobject, residence)
            else:
                # Depart the town and take their nuclear family with them
                depart_town(gameobject)

            gameobject.world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    gameobject.world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )

        super().__init__("FindTheirOwnPlace", p, cb, chance_move_out)


class RetirementEvent(LifeEvent):
    """
    Character retires from their job when they become a senior citizen
    """

    def __init__(self):
        def p(gameobject: GameObject) -> bool:
            character = gameobject.get_component(GameCharacter)
            rng = gameobject.world.get_resource(NeighborlyEngine).get_rng()
            age_min, age_max = character.character_def.lifecycle.age_ranges["senior"]

            return gameobject.has_component(Occupation) and gameobject.get_component(
                GameCharacter
            ).age > max(age_min, int(rng.random() * age_max))

        def cb(gameobject: GameObject, **kwargs) -> None:
            gameobject.add_component(RetiredStatus())

            vacate_job_position(gameobject.get_component(Occupation))

            gameobject.world.get_resource(EventLog).add_event(
                LifeEventRecord(
                    self.name,
                    gameobject.world.get_resource(SimDateTime).to_iso_str(),
                    {"subject": [gameobject.id]},
                ),
                [gameobject.id],
            )
            raise NotImplementedError()

        super().__init__("Retirement", p, cb)


#######################################
#         HELPER FUNCTIONS            #
#######################################


def try_find_housing(world: World) -> Optional[Residence]:
    """
    Attempt to find a vacant residence or build a new one

    Parameters
    ----------
    world: World
        world instance to find housing within

    Returns
    -------
    Optional[Residence]:
        Residence that is available for move in
    """
    raise NotImplementedError()


def move_into_residence(
    character: GameObject, residence: Residence, is_owner: bool = True
) -> None:
    """
    Move a character into a given residence including their nuclear family

    Parameters
    ----------
    character: GameObject
        character
    residence: Residence
        Where the character is moving into
    is_owner: bool
        Is the character one of the owners of the residence
    """
    raise NotImplementedError()


def depart_town(character: GameObject) -> None:
    """
    Given character leaves the town and takes their nuclear family with them

    Parameters
    ----------
    character: GameObject
        Character that is leaving the town
    """
    # 1) Check if the character is a resident and has a location
    # 2) Create a departure LifeEvent Record
    # 3) Decrease the town population
    # 4) Vacate the character from their home
    # 5) Vacate the character from their job
    # 6) Call this function on the rest of the nuclear family
    raise NotImplementedError()


def vacate_job_position(occupation: Occupation) -> None:
    """
    Removes the character as an employee at their current job

    Parameters
    ----------
    occupation: Occupation
        The Occupation that this character currently holds
    """
    raise NotImplementedError()
