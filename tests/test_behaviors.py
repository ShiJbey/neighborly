# import esper
# import pytest


# @pytest.fixture
# def sample_world() -> esper.World:
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

#     city = factory.create()
#     world: esper.World = esper.World()
#     create_business('Restaurant', world)
