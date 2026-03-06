"""
Read a configuration file.
"""

from pathlib import Path
from typing import Any

import yaml


def get_config(config_path: Path) -> dict[str, Any]:
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config
