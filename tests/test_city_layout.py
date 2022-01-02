# import defaults.plugins.default_theme as default_theme_plugin
# import pytest
# from city.city import CityFactory
# from city.layout import Grid, CityLayout, RoadType, Vector2D
# from defaults import LegacyLayoutFactory
# from defaults.city.linear_layout import LinearLayoutFactory


# @pytest.fixture
# def initialize_plugins():
#     default_theme_plugin.initialize_plugin()


# @pytest.mark.usefixtures('initialize_plugins')
# def test_grid():
#     grid: 'Grid[str]' = Grid(10, 2, default_factory=lambda: '*')

#     # Retrieving information
#     assert grid[0, 0] == '*'
#     assert grid[9, 1] == '*'

#     # Setting information
#     grid[9, 1] = 'apples'
#     assert grid[9, 1] == 'apples'
#     with pytest.raises(IndexError):
#         grid[10, 3] = '*'


# @pytest.mark.usefixtures('initialize_plugins')
# def test_linear_layout_generator():
#     layout: 'CityLayout' = LinearLayoutFactory(10, 2).generate_layout()

#     # Make sure that all teh grids are the same size as the world
#     assert layout.shape == (10, 2)
#     assert layout.structure_grid.shape == (10, 2)
#     assert layout.zoning_grid.shape == (10, 2)
#     assert layout.road_grid[0, layout.shape[1] - 1] == RoadType.STRAIGHT_EW
#     assert layout.road_grid[0, layout.shape[1] - 2] == RoadType.EMPTY


# @pytest.mark.usefixtures('initialize_plugins')
# def test_legacy_layout_generator():
#     layout: CityLayout = LegacyLayoutFactory().generate_layout(
#         city_name_factory=CityFactory.city_name_factories['default'],
#         street_name_factory=CityFactory.street_name_factories['default']
#     )

#     assert layout.shape == (28, 28)
#     assert layout.structure_grid.shape == (28, 28)
#     assert layout.zoning_grid.shape == (28, 28)
#     assert layout.road_grid.shape == (28, 28)

#     assert layout.road_grid[0, 1] == RoadType.STRAIGHT_NS
#     assert layout.road_grid[1, 1] == RoadType.EMPTY
#     assert layout.road_grid[27, 26] == RoadType.STRAIGHT_NS
#     assert layout.road_grid[26, 26] == RoadType.EMPTY


# @pytest.mark.usefixtures('initialize_plugins')
# def test_building_on_lots():
#     # Create a town with a single lot
#     layout: 'CityLayout' = LinearLayoutFactory(1).generate_layout()

#     assert len(layout.lots) == 1

#     lot = layout.lots[0]

#     assert lot.position == Vector2D(0, 0)
#     assert lot.occupied == False

#     lot.set_building(1)

#     assert lot.occupied == True

#     lot.set_building(None)

#     assert lot.occupied == False
