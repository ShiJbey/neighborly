"""
helpers.py

This file contains helper functions that can be used to
modify the simulation state in response to certain events
"""


def generate_child_name():
    """Generate the name for a child based"""
    ...


def rename_character(character, name) -> None:
    """Change the name of the character to the given name"""
    ...


def add_neighbor_relationship_flags(character, residence, world) -> None:
    """
    Finds the characters living in adjacent residences and adds
    a neighbor flag to this characters relationship to them in
    the relationship network.
    """
    ...


def remove_neighbor_relationship_flags(character, residence) -> None:
    """
    Remove the neighbor flag from the relationship and add a former-neighbor flags
    for all characters that currently have the neighbor flag
    """
    ...


def combine_families(family_a, family_b):
    """Combines two nuclear families into a single nuclear family component"""
    ...


def move_into_residence(character, family):
    """Moves a character into a home"""
    ...


def add_grieving_status(character):
    """Adds the grieving status to a character"""
    ...


def remove_grieving_status(character):
    """Removes grieving status from character"""
    ...
