import logging
from collections.abc import Mapping
from typing import Any

import senspi.mock.constant_number_readout as num_sens
import senspi.mock.constant_string_readout as str_sens
from senspi.constants import NUMBER_PARAMETERS, STRING_PARAMETERS
from senspi.transform import ReaderType, SchemaType, ValueType, not_special, transform

"""
A sensor that returns a complex, constant value.
Useful for testing.
"""

SCHEMA: SchemaType = {
    "@type": "map",  # map with string keys
    "acceleration": {
        "@type": "map",
        "x": {"@type": "float", "@defaults": NUMBER_PARAMETERS},
        "y": {"@type": "float", "@defaults": NUMBER_PARAMETERS},
        "z": {"@type": "float", "@defaults": NUMBER_PARAMETERS},
    },
    "giroscope": {
        "@type": "array",  # sequence of items of same type
        "@items": {"@type": "float", "@defaults": NUMBER_PARAMETERS},
    },
    "atmosphere": {
        "@type": "tuple",  # sequence of specific length and types
        "@items": [
            {"@type": "float", "@defaults": NUMBER_PARAMETERS},
            {"@type": "string", "@defaults": STRING_PARAMETERS},
        ],
    },
    "temperature": {"@type": "float", "@defaults": NUMBER_PARAMETERS},
}

log = logging.getLogger(__name__)


def make_value(schema) -> ValueType:
    """Build a complex value conforming to `schema`
    using the constants defined in this file"""

    value_type = schema.get("@type", None)
    if value_type == "map":
        value = {}
        for k, v in filter(not_special, schema.items()):
            value[k] = make_value(v)
        return value
    elif value_type == "array":
        value = []
        item = make_value(schema["@items"])
        for _ in range(3):  # in practice, arrays can be any length
            value.append(item)
        return value
    elif value_type == "tuple":
        value = []
        for item_type in schema["@items"]:
            value.append(make_value(item_type))
        return value
    elif value_type == "float":
        return num_sens.VALUE
    elif value_type == "string":
        return str_sens.VALUE
    else:
        msg = f"unknown type in schema {value_type}"
        log.error(msg)
        raise ValueError(msg)


def initialize(params: Mapping[str, Any]) -> ReaderType:
    value = transform(make_value(SCHEMA), params)

    def read() -> ValueType:
        return value

    return read
