import json

import yaml


from neighborly.simulation import (
    NeighborlyConfig,
    PluginConfig,
    Simulation,
    SimulationConfig,
)


def test_construct_simulation_config():
    """
    Test that simulation configurations are properly
    constructed from YAML and JSON
    """

    yaml_str = """
        seed: 20203
        hours_per_timestep: 8
        start_date: "2000-00-00"
        end_date: "2030-00-00"
        town:
            name: "Pizzaville"
        """

    yaml_data = yaml.safe_load(yaml_str)

    config_from_yaml = SimulationConfig(**yaml_data)

    assert 20203 == config_from_yaml.seed
    assert 8 == config_from_yaml.hours_per_timestep
    assert "2000-00-00" == config_from_yaml.start_date
    assert "2030-00-00" == config_from_yaml.end_date
    assert "Pizzaville" == config_from_yaml.town.name

    json_str = """
        {
            "seed": 20210,
            "hours_per_timestep": 4,
            "start_date": "2010-06-00",
            "end_date": "2035-00-00",
            "town": {
                "name": "Apple World"
            }
        }
        """

    json_data = json.loads(json_str)

    config_from_json = SimulationConfig(**json_data)

    assert 20210 == config_from_json.seed
    assert 4 == config_from_json.hours_per_timestep
    assert "2010-06-00" == config_from_json.start_date
    assert "2035-00-00" == config_from_json.end_date
    assert "Apple World" == config_from_json.town.name


def test_construct_neighborly_config():
    """
    Test that Neighborly configurations are properly
    constructed from YAML and JSON
    """

    yaml_str = """
        simulation:
            seed: 20203
            hours_per_timestep: 8
            start_date: "2000-00-00"
            end_date: "2030-00-00"
            town:
                name: "Pizzaville"
        plugins:
            - "neighborly.plugin.defaults"
            - "neighborly-talktown"
        """

    yaml_data = yaml.safe_load(yaml_str)
    config_from_yaml = NeighborlyConfig(**yaml_data)
    assert "neighborly.plugin.defaults" == config_from_yaml.plugins[0]
    assert "neighborly-talktown" == config_from_yaml.plugins[1]

    json_str = """
        {
            "simulation": {
                "seed": 20210,
                "hours_per_timestep": 4,
                "start_date": "2010-06-00",
                "end_date": "2035-00-00",
                "town": {
                    "name": "Apple World"
                }
            },
            "plugins": [
                "neighborly.plugin.defaults",
                {
                    "name": "neighborly-talktown",
                    "options": {
                        "arg0": "pizza"
                    }
                }
            ]
        }
        """

    json_data = json.loads(json_str)
    config_from_json = NeighborlyConfig(**json_data)
    assert "neighborly.plugin.defaults" == config_from_json.plugins[0]
    assert isinstance(config_from_json.plugins[1], PluginConfig)
    assert "neighborly-talktown" == config_from_json.plugins[1].name
    assert "pizza" == config_from_json.plugins[1].options["arg0"]


def test_neighborly_config_from_partial():
    """
    Test that NeighborlyConfig.from_partial()
    constructs valid config objects given a
    default starting object and a dict of fields
    to overwite
    """

    default_config = NeighborlyConfig(
        simulation=SimulationConfig(
            seed=10,
            hours_per_timestep=6,
            start_date="0000-00-00T00:00.000z",
            end_date="0100-00-00T00:00.000z",
        ),
        plugins=["neighborly.plugins.default"],
    )

    custom_config = {
        "simulation": {"seed": 909, "hours_per_timestep": 8},
        "plugins": ["custom_plugin"],
    }

    config = NeighborlyConfig.from_partial(custom_config, default_config)
    assert "custom_plugin" == config.plugins[0]
    assert 1 == len(config.plugins)
    assert 909 == config.simulation.seed
    assert 8 == config.simulation.hours_per_timestep


def test_constructing_plugins():
    """
    Tests constructing plugins given the name of a module or
    package where to find the package
    """
    config = NeighborlyConfig(
        simulation=SimulationConfig(
            seed=10,
            hours_per_timestep=6,
            start_date="0000-00-00T00:00.000z",
            end_date="0100-00-00T00:00.000z",
        ),
        plugins=[],
    )

    sim = Simulation(config)

    sim._dynamic_load_plugin("neighborly.plugins.default_plugin")
