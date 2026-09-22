from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def test_configuration_templates_are_valid_yaml() -> None:
    config_files = sorted((ROOT / "configs").glob("*.yaml"))

    assert config_files
    for config_file in config_files:
        with config_file.open(encoding="utf-8") as stream:
            assert yaml.safe_load(stream) is not None


def test_package_metadata_is_available() -> None:
    from traffic_control import __version__

    assert __version__ == "0.1.0"


def test_phase_zero_repository_files_exist() -> None:
    required_files = [
        ".gitignore",
        "CHANGELOG.md",
        "EXPERIMENT_LOG.md",
        "PROJECT_STATUS.md",
        "pyproject.toml",
        "README.md",
    ]

    assert all((ROOT / file_name).is_file() for file_name in required_files)
