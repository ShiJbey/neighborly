# import defaults.plugins.default_theme as default_theme_plugin
# import esper
# import pytest
# from character import Character, select_favorite_activities
# from character import Unemployed
# from character.activitytracker import Activity
# from character.propensity import Propensities
# from theme_manager import ThemeManager


# @pytest.fixture
# def initialize_plugins():
#     default_theme_plugin.initialize_plugin()


# @pytest.fixture
# def simple_activities():
#     Activity.register_activity(
#         Activity('mourning', 'thats rough buddy', ['depression']))
#     Activity.register_activity(Activity(
#         'flirting', 'spitting game at the other agents', ['lustful', 'love']))
#     Activity.register_activity(
#         Activity('quiting', 'you\'ve tried this before', ['rashness']))


# @pytest.mark.usefixtures('simple_activities')
# def test_select_favorite_activities():
#     rls_propensities = Propensities({
#         "rashness": 90,
#         "lustful": 90,
#         "social": 90
#     })

#     assert select_favorite_activities(1, rls_propensities) == ['flirting']


# @pytest.mark.usefixtures('initialize_plugins', 'simple_activities')
# def test_create_character():
#     world: esper.World = esper.World()

#     person = ThemeManager.create_character("Person", world)

#     character_component = world.component_for_entity(person, Character)

#     character_component.statuses.add_status(Unemployed(person))

#     # people should always start off unemployed
#     assert character_component.statuses.has_status('Unemployed') == True
#     assert type(person) == int
