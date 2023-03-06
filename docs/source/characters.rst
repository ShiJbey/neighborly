Characters
==========

Characters are modeled GameObjects (entities) represent.


Character prefabs are defined using YAML configuration files. These files define what components
are attached to characters at spawn and their probability of spawning into a Settlement. Below
is an example of a prefab. There is a lot going on here. Each piece is explained afterward.

.. code-block:: yaml

    name: SampleCharacter
    is_template: no
    spawn_frequency: 2
    components:
        GameCharacter:
            first_name: "#character::default::first_name::gender-neutral#"
            last_name: "#character::default::last_name#"
        AgingConfig:
            adolescent_age: 13
            young_adult_age: 18
            adult_age: 30
            senior_age: 65
        Lifespan:
            value: 85
        MarriageConfig:
            spouse_prefabs:
            - "character::default::.*"
            chance_spawn_with_spouse: 0.5
        ReproductionConfig:
            max_children_at_spawn: 3
            child_prefabs:
            - "character::default::.*"
        RelationshipManager: { }
        Virtues: { }
        CanAge: { }
        StatusManager: { }
        TraitManager: { }
        FrequentedLocations: { }
        AIComponent:
            brain: "default"
        EventHistory: { }
        Age: { }
