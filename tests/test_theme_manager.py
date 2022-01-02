# import pytest
# from business import Occupation
# from character import Character
# from theme_manager import load_characters, load_occupations


# @pytest.fixture
# def custom_characters() -> str:
#     return """
#     Android: {}

#     Ewok:
#         life_cycle:
#             adult_age: 5
#             avg_lifespan_years: 35

#     Goblin:
#         life_cycle:
#             avg_lifespan_years: 150
#     """


# @pytest.fixture
# def custom_occupations() -> str:
#     return """
#     Proprietor:
#         level: 2
#         activities:
#             - managing
#             - going over the books
#             - reviewing payroll

#     Waiter:
#         level: 1
#         activities:
#             - serving tables

#     Cook:
#         level: 1
#         activities:
#             - cooking
#             - on smoke break

#     Busboy:
#         level: 1
#         activities:
#             - bussing tables

#     Manager:
#         level: 2
#         activities:
#             - going over the books
#             - reviewing payroll
#             - taking inventory

#     Dishwasher:
#         level: 1
#         activities:
#             - washing dishes

#     Bartender:
#         level: 2
#         activities:
#             - serving drinks
#             - restocking the bar


#     Office Worker:
#         level: 3
#         required_education: secondary
#         activities:
#             - doing paperwork
#             - reviewing spreadsheets

#     Intern:
#         level: 1
#         activities:
#             - playing solitaire
#             - making copies
#             - reading

#     Salesperson:
#         level: 2
#         activities:
#             - calling clients
#             - reviewing sales numbers

#     CEO:
#         level: 5
#         required_education: college
#         activities:
#             - teleconferencing with clients
#             - meeting with shareholders
#     """


# def test_load_characters(custom_characters):
#     load_characters(yaml_str=custom_characters)

#     assert 'Android' in Character.character_configs
#     assert 'Ewok' in Character.character_configs
#     assert 'Goblin' in Character.character_configs

#     assert Character.character_configs['Ewok'].life_cycle.adult_age == 5
#     assert Character.character_configs['Ewok'].life_cycle.avg_lifespan_years == 35

#     assert Character.character_configs['Goblin'].life_cycle.adult_age == 18
#     assert Character.character_configs['Goblin'].life_cycle.avg_lifespan_years == 150


# def test_load_occupations(custom_occupations):
#     load_occupations(yaml_str=custom_occupations)

#     assert 'Proprietor' in Occupation.config_registry
#     assert 'CEO' in Occupation.config_registry
#     assert 'Manager' in Occupation.config_registry
