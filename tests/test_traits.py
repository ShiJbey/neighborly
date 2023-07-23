from neighborly import Neighborly
from neighborly.components.character import CanGetOthersPregnant, Immortal
from neighborly.components.trait import Traits


def test_traits_factory():
    sim = Neighborly()

    game_obj = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(
                Traits,
                traits=[
                    "Immortal"
                ]
            )
        ]
    )

    assert game_obj.has_component(Traits)
    assert game_obj.has_component(Immortal)

    sim = Neighborly()

    game_obj = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(
                Traits,
                traits=[
                    "Immortal | CanGetOthersPregnant"
                ]
            )
        ]
    )

    if game_obj.has_component(Immortal):
        assert game_obj.has_component(CanGetOthersPregnant) is False

    elif game_obj.has_component(CanGetOthersPregnant):
        assert game_obj.has_component(Immortal) is False

    assert game_obj.has_component(Traits)
