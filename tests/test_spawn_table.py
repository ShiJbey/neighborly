from neighborly.spawn_table import CharacterSpawnTable


def test_character_library_get_matching_entries():
    table = CharacterSpawnTable()

    table.update("human:male", 1)
    table.update("human:female", 1)
    table.update("orc:male", 1)
    table.update("orc:female", 1)
    table.update("android", 1)
    table.update("elf:dark:male", 1)
    table.update("elf:woodland:female", 1)

    assert table.get_matching_prefabs("human:*") == [
        "human:male", "human:female"
    ]

    assert table.get_matching_prefabs("orc:*") == [
        "orc:male", "orc:female"
    ]

    assert table.get_matching_prefabs("elf:dark:*") == [
        "elf:dark:male"
    ]
