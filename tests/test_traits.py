from neighborly import Neighborly
from neighborly.components.character import Immortal
from neighborly.traits import Traits


def test_traits_factory():
    sim = Neighborly()

    game_obj = sim.world.gameobject_manager.spawn_gameobject(
        components={Traits: {}, Immortal: {}},
    )

    assert game_obj.has_component(Traits)
    assert game_obj.has_component(Immortal)
