# import pytest

# from character.activitytracker import Activity


# @pytest.fixture
# def simple_activities():
#     Activity.register_activity(
#         Activity('mourning', 'thats rough buddy', ['depression']))
#     Activity.register_activity(Activity(
#         'flirting', 'spitting game at the other agents', ['lustful', 'love']))
#     Activity.register_activity(
#         Activity('quiting', 'you\'ve tried this before', ['rashness']))


# @pytest.mark.usefixtures('simple_activities')
# def test_get_activity():
#     assert Activity.activity_registry['flirting'].name == 'flirting'
#     assert Activity.activity_registry['flirting'].propensities['lustful'] == 1
#     assert Activity.activity_registry['flirting'].propensities['envy'] == 0
