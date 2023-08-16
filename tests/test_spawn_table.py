from neighborly.spawn_table import CharacterSpawnTable, CharacterSpawnTableEntry


def test_character_library_get_matching_entries():
    table = CharacterSpawnTable()

    table.update(CharacterSpawnTableEntry(name="human:male", spawn_frequency=1))
    table.update(CharacterSpawnTableEntry(name="human:female", spawn_frequency=1))
    table.update(CharacterSpawnTableEntry(name="orc:male", spawn_frequency=1))
    table.update(CharacterSpawnTableEntry(name="orc:female", spawn_frequency=1))
    table.update(CharacterSpawnTableEntry(name="android", spawn_frequency=1))
    table.update(CharacterSpawnTableEntry(name="elf:dark:male", spawn_frequency=1))
    table.update(
        CharacterSpawnTableEntry(name="elf:woodland:female", spawn_frequency=1)
    )

    assert table.get_matching_names("human:*") == ["human:male", "human:female"]

    assert table.get_matching_names("orc:*") == ["orc:male", "orc:female"]

    assert table.get_matching_names("elf:dark:*") == ["elf:dark:male"]
