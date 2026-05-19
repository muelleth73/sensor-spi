"""
Read a configuration file.
"""

import logging
import logging.config
from pathlib import Path

import yaml

from senspi.transform import SchemaType

p = Path(__file__).parents[2].resolve()
logging.config.fileConfig(p / "config" / "logging.conf")


def init_logging(path: Path):
    """
    Re-initialize logging with the file at `path`.

    Calling this is optional - logging will have been configured
    at the module level (see above).
    """
    logging.config.fileConfig(path)


def get_logger(name: str) -> logging.Logger:
    """
    Return the named logger.
    """
    return logging.getLogger(name)


"""
Typical usage of get_logger
This will return the name of this module, 
unless it is executing as the top-level module
in which case the logger will be called '__main__'.
"""
log = get_logger(__name__)


def get_root_logger() -> logging.Logger:
    """
    "Return the root logger.
    """
    return logging.getLogger()


def get_config(config_path: Path) -> SchemaType:
    """
    Find, load and return the configuration at `config_path`.

    """
    with open(config_path) as f:
        config = yaml.safe_load(f)
        if config is not None:
            return config
        else:
            log.error(f"failed to load config from {config_path}")
            return {}
