from pprint import pprint
from neighborly.core.character import GameCharacter
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.life_event import LifeEventLogger
from neighborly.simulation import Simulation


def list_characters(sim: Simulation) -> None:
    """Print the IDs, names, ages, and locations of all the characters"""
    print("{:30s} {:25s} {:5s}".format("ID", "Name", "Age"))
    for gid, character in sim.world.get_component(GameCharacter):
        print(f"{gid:<30} {str(character.name)!r:<25} {int(character.age):<5}")


def list_relationships(sim: Simulation, character_id: int) -> None:
    """List the relationships for a single character"""
    gameobject = sim.world.get_gameobject(character_id)
    character = gameobject.get_component(GameCharacter)

    relationship_net = sim.world.get_resource(RelationshipNetwork)

    relationships = relationship_net.get_relationships(character_id)

    print(f"Showing {len(relationships)} relationships for: {str(character.name)}")

    print("{:30s} {:12s} {:12s}".format("Target", "Friendship", "Romance"))
    for r in relationships:
        print(f"{r.target:<30} {r.friendship:<12} {r.romance:<12}")


def display_gameobject(sim: Simulation, gid: int) -> None:
    pprint(sim.world.get_gameobject(gid).to_dict())


def list_event_history(sim: Simulation, gid: int) -> None:
    event_logger = sim.world.get_resource(LifeEventLogger)

    for e in event_logger.get_events_for(gid):
        print(str(e))
