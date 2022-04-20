import logging
from typing import Optional, Dict, Any

from neighborly.core.business import Business, OccupationDefinition, Occupation
from neighborly.core.character.character import GameCharacter
from neighborly.core.ecs import GameObject
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent, EventLog, LifeEventRecord
from neighborly.core.location import Location
from neighborly.core.residence import Residence
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.status import Status
from neighborly.core.time import SimDateTime
from neighborly.plugins.default_plugin.statuses import DatingStatus, MarriedStatus, AdultStatus

logger = logging.getLogger(__name__)


class DeathEvent(LifeEvent):

    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""
            character = gameobject.get_component(GameCharacter)
            return character.alive and character.age >= character.max_age

        # end precondition

        def cb(gameobject: GameObject, options: Optional[Dict[str, Any]] = None) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            logger.debug(
                f"{str(character.name)} died at the age of {round(character.age)}")

            character.alive = False

            if character.location:
                world.get_gameobject(character.location).get_component(Location).remove_character(
                    character.gameobject.id)

            home_id = character.location_aliases.get("home")
            if home_id:
                world.get_gameobject(home_id).get_component(
                    Residence).remove_tenant(character.gameobject.id)

            world.get_resource(RelationshipNetwork).remove_node(
                character.gameobject.id)

            world.get_resource(EventLog).add_event(
                LifeEventRecord(self.name, world.get_resource(
                    SimDateTime).to_iso_str(), {"subject": [gameobject.id]}),
                [gameobject.id])

            world.delete_gameobject(character.gameobject.id)

        # end callback

        super().__init__("Death", p, cb, 0.8)


class BecameAdultEvent(LifeEvent):

    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""
            character = gameobject.get_component(GameCharacter)
            return character.alive and character.age >= character.character_def.lifecycle.adult_age \
                   and not gameobject.get_component(AdultStatus)

        # end precondition

        def cb(gameobject: GameObject, options: Optional[Dict[str, Any]] = None) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} became and adult")
            character.gameobject.add_component(AdultStatus())
            world.get_resource(EventLog).add_event(
                LifeEventRecord(self.name, world.get_resource(
                    SimDateTime).to_iso_str(), {"subject": [gameobject.id]}),
                [gameobject.id])

        # end callback

        super().__init__("Became Adult", p, cb)


class BecameSeniorEvent(LifeEvent):

    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""
            character = gameobject.get_component(GameCharacter)
            return character.age >= character.config.lifecycle.senior_age \
                   and not character.gameobject.get_component(StatusManager).has_status("Senior")

        # end precondition

        def cb(gameobject: GameObject, options: Optional[Dict[str, Any]] = None) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} became and senior")
            character.gameobject.get_component(
                StatusManager).add_status(Status.create("Senior"))
            world.get_resource(EventLog).add_event(
                LifeEventRecord(self.name, world.get_resource(
                    SimDateTime).to_iso_str(), {"subject": [gameobject.id]}),
                [gameobject.id])

        # end callback

        super().__init__("Became Senior", p, cb)


class BecameUnemployedEvent(LifeEvent):

    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""
            character = gameobject.get_component(GameCharacter)
            status_manager = gameobject.get_component(StatusManager)
            return status_manager.has_status("Adult") \
                   and not status_manager.has_status("Unemployed")

        # end precondition

        def cb(gameobject: GameObject, options: Optional[Dict[str, Any]] = None) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} became unemployed")
            character.gameobject.get_component(
                StatusManager).add_status(Status.create("Unemployed"))
            world.get_resource(EventLog).add_event(
                LifeEventRecord(self.name, world.get_resource(
                    SimDateTime).to_iso_str(), {"subject": [gameobject.id]}),
                [gameobject.id])

        # end callback

        super().__init__("Became Unemployed", p, cb)


class BecameBusinessOwnerEvent(LifeEvent):

    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Characters get hired if they are unemployed"""
            status_manager = gameobject.get_component(StatusManager)
            is_unemployed = status_manager.has_status("Unemployed")

            # There is a business that needs an owner
            businesses_without_owners = list(filter(
                lambda res: res[1].needs_owner(),
                gameobject.world.get_component(Business)
            ))

            return is_unemployed and businesses_without_owners

        # end precondition

        def cb(gameobject: GameObject, options: Optional[Dict[str, Any]] = None) -> None:
            """Remove the character from the world"""
            businesses_without_owners = list(filter(
                lambda res: res[1].needs_owner(),
                gameobject.world.get_component(Business)
            ))

            business_id, business = businesses_without_owners[0]

            owner_typename = business.get_type().owner

            if owner_typename is None:
                raise RuntimeError(
                    "Missing owner occupation type for business that needs owner")

            occupation_type = OccupationDefinition.get_registered_type(
                owner_typename)

            gameobject.add_component(Occupation(occupation_type, business_id))

            character = gameobject.get_component(GameCharacter)

            business.hire_owner(character.gameobject.id)

            world = gameobject.world

            logger.debug(
                f"{str(character.name)} became owner of {business.get_name()}")

            character.gameobject.get_component(
                StatusManager).remove_status("Unemployed")

            world.get_resource(EventLog).add_event(
                LifeEventRecord(self.name, world.get_resource(SimDateTime).to_iso_str(),
                                {"subject": [gameobject.id], "business": business_id}),
                [gameobject.id])

        # end callback

        super().__init__("Became Business Owner", p, cb)


class GetHiredEvent(LifeEvent):

    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Characters get hired if they are unemployed"""
            status_manager = gameobject.get_component(StatusManager)
            is_unemployed = status_manager.has_status("Unemployed")

            # There is a business with vacancies
            businesses = gameobject.world.get_component(Business)

            return is_unemployed

        # end precondition

        def cb(gameobject: GameObject, options: Optional[Dict[str, Any]] = None) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world
            logger.debug(f"{str(character.name)} got hired")
            character.gameobject.get_component(
                StatusManager).remove_status("Unemployed")
            world.get_resource(EventLog).add_event(
                LifeEventRecord(self.name, world.get_resource(
                    SimDateTime).to_iso_str(), {"subject": [gameobject.id]}),
                [gameobject.id])

        # end callback

        super().__init__("Get Hired", p, cb)


class StartedDatingEvent(LifeEvent):

    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""
            if gameobject.get_component(StatusManager).has_status("Dating"):
                return False

            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            relationship_net = world.get_resource(RelationshipNetwork)

            love_interests = relationship_net.get_all_relationships_with_tags(
                character.gameobject.id,
                "Love Interest"
            )

            love_interests_that_know_you = [relationship_net.get_connection(r.target, character.gameobject.id) for r in
                                            love_interests if
                                            relationship_net.has_connection(r.target, character.gameobject.id)]

            single_love_interests = [li for li in love_interests_that_know_you if
                                     not gameobject.world.get_gameobject(li.owner).get_component(
                                         StatusManager).has_status("Dating")]

            return any([r.has_tags("Love Interest") for r in single_love_interests])

        # end precondition

        def cb(gameobject: GameObject, options: Optional[Dict[str, Any]] = None) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            relationship_net = world.get_resource(RelationshipNetwork)

            love_interests = relationship_net.get_all_relationships_with_tags(
                character.gameobject.id,
                "Love Interest"
            )

            love_interests_that_know_you = list(filter(
                lambda rel: rel.has_tags("Love Interest"),
                [relationship_net.get_connection(r.target, character.gameobject.id) for r in
                 love_interests if
                 relationship_net.has_connection(r.target, character.gameobject.id)]))

            single_love_interests = [li for li in love_interests_that_know_you if
                                     not gameobject.has_component(DatingStatus)]

            potential_mate: int = \
                world.get_resource(NeighborlyEngine).get_rng().choice(
                    single_love_interests).owner

            world.get_resource(EventLog).add_event(
                LifeEventRecord(self.name, world.get_resource(SimDateTime).to_iso_str(),
                                {"subject": [gameobject.id, potential_mate]}),
                [gameobject.id, potential_mate])

            world.get_gameobject(potential_mate).add_component(
                DatingStatus(gameobject.id,
                             str(gameobject.get_component(GameCharacter).name)))

            gameobject.add_component(
                DatingStatus(potential_mate,
                             str(world.get_gameobject(potential_mate).get_component(GameCharacter).name)))

            logger.debug(
                f"{str(character.name)} and {str(world.get_gameobject(potential_mate).get_component(GameCharacter).name)} started dating")

        # end callback

        super().__init__("Dating", p, cb)


class DatingBreakUpEvent(LifeEvent):

    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Break up with your partner if you're not one of their love interests"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            if not gameobject.get_component(StatusManager).has_status("Dating"):
                return False

            dating_status = character.gameobject.get_component(
                StatusManager).get_status("Dating")

            partner_id: int = dating_status["partner_id"]

            relationship_net = world.get_resource(RelationshipNetwork)

            # rel = relationship_net.get_connection(partner_id, gameobject.id)
            #
            # if character.gameobject.id not in partner_love_interests:
            #     return True

            return False

        # end precondition

        def cb(gameobject: GameObject, options: Optional[Dict[str, Any]] = None) -> None:
            """Remove the dating status"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            dating_status = character.gameobject.get_component(
                StatusManager).get_status("Dating")

            partner_id: int = dating_status["partner_id"]
            partner_name: int = dating_status["partner_name"]

            partner = world.get_gameobject(partner_id)

            partner.get_component(StatusManager).remove_status("Dating")
            character.gameobject.get_component(
                StatusManager).remove_status("Dating")

            logger.debug(
                f"{str(character.name)} and {str(partner_name)} broke up")

            world.get_resource(EventLog).add_event(
                LifeEventRecord(self.name, world.get_resource(SimDateTime).to_iso_str(),
                                {"subject": [gameobject.id, partner_id]}), [gameobject.id, partner_id])

        # end callback

        super().__init__("Break Up", p, cb)


class MarriageEvent(LifeEvent):

    def __init__(self) -> None:
        def p(gameobject: GameObject) -> bool:
            """Die if they are older than a certain age and not immortal"""
            character = gameobject.get_component(GameCharacter)
            status_manager = character.gameobject.get_component(StatusManager)
            return status_manager.has_status("Dating")

        # end precondition

        def cb(gameobject: GameObject, options: Optional[Dict[str, Any]] = None) -> None:
            """Remove the character from the world"""
            character = gameobject.get_component(GameCharacter)
            world = gameobject.world

            status_manager = character.gameobject.get_component(StatusManager)
            status = status_manager.get_status("Dating")
            status_manager.remove_status("Dating")

            partner_id: int = status['partner_id']
            partner_name: str = status['partner_name']

            # Remove dating status from characters
            status_manager.remove_status("Dating")
            world.get_gameobject(partner_id).get_component(
                StatusManager).remove_status("Dating")

            # Add Married status to characters
            status_manager.add_status(MarriedStatus(partner_id, partner_name))
            world.get_gameobject(partner_id).get_component(StatusManager).add_status(
                MarriedStatus(character.gameobject.id, str(character.name)))

            world.get_resource(EventLog).add_event(
                LifeEventRecord(self.name, world.get_resource(SimDateTime).to_iso_str(),
                                {"subject": [gameobject.id, partner_id]}), [gameobject.id, partner_id])

            logger.debug(
                f"{str(character.name)} and {str(partner_name)} got married.")

        # end callback

        super().__init__("Marriage", p, cb)
