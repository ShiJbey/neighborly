from neighborly import NeighborlyConfig
from neighborly.config import PluginConfig


def test_cli_config_from_partial() -> None:
    existing_config = NeighborlyConfig(
        years_to_simulate=50,
    )

    overwritten_config = NeighborlyConfig.from_partial(
        {"seed": "apples", "plugins": [{"name": "sample_plugin"}]}, existing_config
    )

    assert overwritten_config.seed == "apples"

    plugin_info = overwritten_config.plugins[0]
    assert isinstance(plugin_info, PluginConfig)
    assert plugin_info.name == "sample_plugin"
