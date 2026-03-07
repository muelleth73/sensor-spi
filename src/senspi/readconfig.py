"""
Read a configuration file.
"""

import logging
from pathlib import Path

import yaml

from senspi.transform import SchemaType

log = logging.getLogger(__name__)


def get_config(config_path: Path) -> SchemaType:
    with open(config_path) as f:
        config = yaml.safe_load(f)
        if config is not None:
            return config
        else:
            log.error(f"failed to load config from {config_path}")
            return {}
