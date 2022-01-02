# import defaults.plugins.default_theme as default_theme_plugin
# import esper
# import pytest
# from behavior_tree import Blackboard, NodeState
# from city.city import City, CityFactory, CityLayoutFactory, CityLayout
# from processors import get_city
# from simulation import AddBusinessBehavior, AddResidentsBehavior


# @pytest.fixture
# def single_lot_town() -> City:
#     default_theme_plugin.initialize_plugin()

#     class SingleLotLayoutFactory(CityLayoutFactory):

#         def generate_layout(self, **kwargs) -> CityLayout:
#             del kwargs
#             layout = CityLayout(1, 1)
#             layout.zone_lot((0, 0))
#             return layout

#     CityFactory.city_name_factories['default'] = \
#         lambda: 'Single Lot Town'

#     factory = CityFactory(SingleLotLayoutFactory())

#     return factory.create()


# def test_city_factory(single_lot_town: City):
#     assert single_lot_town.name == 'Single Lot Town'
#     assert len(single_lot_town.layout.lots) == 1
#     single_lot_town.name = 'Pizza Town'


# def test_add_resident(single_lot_town: City):
#     world = esper.World()

#     world.create_entity(single_lot_town)

#     add_resident_bt = AddResidentsBehavior()

#     result = add_resident_bt.evaluate(Blackboard({
#         'world': world,
#     }))

#     assert result == NodeState.SUCCESS

#     city = get_city(world)

#     assert len(city.residents) == 1

#     result = add_resident_bt.evaluate(Blackboard({
#         'world': world,
#     }))

#     assert result == NodeState.FAILURE


# def test_add_business(single_lot_town: City):
#     world = esper.World()

#     world.create_entity(single_lot_town)

#     add_business_bt = AddBusinessBehavior()

#     result = add_business_bt.evaluate(Blackboard({
#         'world': world,
#     }))

#     assert result == NodeState.SUCCESS

#     city = get_city(world)

#     assert len(city.businesses) == 1

#     result = add_business_bt.evaluate(Blackboard({
#         'world': world,
#     }))

#     assert result == NodeState.FAILURE
