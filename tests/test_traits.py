from neighborly import Neighborly
from neighborly.components.character import HealthDecay, Immortal
from neighborly.stats import Stats
from neighborly.traits import Traits


def test_traits_factory():
    sim = Neighborly()

    game_obj = sim.world.gameobject_manager.spawn_gameobject(
        components={Traits: {}, Stats: {}, HealthDecay: {}, Immortal: {}},
    )

    assert game_obj.has_component(Traits)
    assert game_obj.has_component(Immortal)
