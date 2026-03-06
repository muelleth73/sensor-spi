import logging
from collections.abc import Callable, Mapping
from typing import Any

from senspi.constants import STRING_PARAMETERS
from senspi.transform import ReaderType, ValueType

"""
An implementation of the sensor interface that returns a constant value.
Useful for testing.
"""

VALUE = "test value with non-ÄsçÎí characters"

SCHEMA = {
    "@type": "string",
    "@defaults": STRING_PARAMETERS,
}

log = logging.getLogger(__name__)


def initialize(params: Mapping[str, Any]) -> ReaderType:
    log.info(f"Initialized constant_string_readout, parameters {params}")

    def read() -> ValueType:
        return VALUE

    return read
