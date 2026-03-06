import logging
from collections.abc import Mapping
from typing import Any

from senspi.constants import NUMBER_PARAMETERS
from senspi.transform import ReaderType, ValueType

"""
An implementation of the sensor interface that returns a constant value.
Useful for testing.
"""

VALUE = 1359.8

SCHEMA = {
    "@type": "float",
    "@defaults": NUMBER_PARAMETERS,
}

NO_DEFAULTS_SCHEMA = {
    "@type": "float",
}

log = logging.getLogger(__name__)


def initialize(params: Mapping[str, Any]) -> ReaderType:
    log.info(f"Initialized constant_number_readout, parameters {params}")

    def read() -> ValueType:
        return VALUE

    return read
