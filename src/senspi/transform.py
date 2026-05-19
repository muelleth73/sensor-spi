"""
Fill in default values, transform raw readouts.
"""

import logging
from collections.abc import Callable, Mapping
from typing import Any

from senspi import constants

log = logging.getLogger(__name__)

type SchemaType = Mapping[str, SchemaType | list[SchemaType] | str | float | int]
type ParameterType = Mapping[str, Any] | list[Any]
type Number = float | int
type ValueType = Number | str | list[ValueType] | Mapping[str, ValueType]
type ReaderType = Callable[[], ValueType]


def not_special(kv_tuple: tuple[str, Any]) -> bool:
    """A predicate that identifies dictionary items (key-value tuples)
    that are not considered 'special' in the sensor schema, i.e. whose
    key does not start with a '@' character
    """

    if kv_tuple[0].startswith("@"):
        return False
    else:
        return True


def add_defaults(schema: SchemaType, parameters: ParameterType) -> ParameterType:
    """
    Add default values from the schema to the parameters.
    """
    typ = schema.get("@type", None)
    if typ == "map":
        items = {}
        assert isinstance(parameters, Mapping)
        for k, v in filter(not_special, schema.items()):
            assert isinstance(v, Mapping)
            items[k] = add_defaults(v, parameters.get(k, {}))
        items["@type"] = "map"
        return items
    elif typ == "array":
        element_type = schema.get("@items", {})
        assert isinstance(element_type, Mapping)
        element = add_defaults(element_type, parameters)
        return {"@type": "array", "@items": element}
    elif typ == "tuple":
        items = []
        para_idx = 0
        assert isinstance(parameters, list)
        tuple_items = schema.get("@items", {})
        assert isinstance(tuple_items, list)
        for element_type in tuple_items:
            assert isinstance(element_type, Mapping)
            items.append(add_defaults(element_type, parameters[para_idx]))
            para_idx += 1
        return {"@type": "tuple", "@items": items}
    elif typ == "float" or typ == "string":
        assert isinstance(parameters, Mapping)
        defaults = schema.get("@defaults", {})
        params = parameters.get("@parameters", {})
        return {"@type": typ, "@parameters": defaults | params}
    else:
        raise ValueError(f"add_defaults error unknown type {typ} in {schema}")


def safe_divisor(x: float) -> float:
    """
    check a potential divisor is not too small, fix otherwise
    """
    if abs(x) < constants.MIN_DIVISOR:
        x = constants.MIN_DIVISOR if x > 0 else -constants.MIN_DIVISOR
        log.warning(f"divisor magniture too small, forced to {x}")
    return x


def transform(value: ValueType, param_map: ParameterType) -> ValueType:
    """Transform a value according to a map of parameters

    For numbers, apply a linear transformation.
    For strings, convert case and/or trim.

    If the current value is not significantly different
    from the previous value, flag the returned value
    as filtered.

    Return a new map of the same structure as `value_map`
    """

    if isinstance(value, dict):
        out_map = {}
        for k, v in value.items():
            assert isinstance(param_map, Mapping)
            if k in param_map:
                out_map[k] = transform(v, param_map[k])
            else:
                out_map[k] = v
        return out_map
    elif isinstance(value, list):
        out_list = []
        param_index = 0
        for item in value:
            if isinstance(param_map, dict):
                params = param_map
            else:
                assert isinstance(param_map, list)
                params = param_map[param_index]
            if params is not None:
                out_list.append(transform(item, params))
            else:
                out_list.append(item)
            param_index = param_index + 1
        return out_list
    elif isinstance(value, int | float):
        assert isinstance(param_map, Mapping)
        p = param_map.get("@parameters", {})
        offset = p.get("offset", 0.0)
        multiplier = p.get("multiplier", 1.0)
        divisor = safe_divisor(p.get("divisor", 1.0))
        new_value = (value - offset) * multiplier / divisor
        return new_value
    elif isinstance(value, str):
        assert isinstance(param_map, Mapping)
        p = param_map.get("@parameters", {})
        target_case = p.get("case", None)
        if target_case == "upper":
            string_value = value.upper()
        elif target_case == "lower":
            string_value = value.lower()
        else:
            string_value = value
        target_length = p.get("trim", None)
        if target_length is not None:
            assert isinstance(string_value, str)
            try:
                target_length = int(target_length)
                if target_length < 1:
                    log.warning(f"trim value too low: {target_length}, ignoring")
                else:
                    string_value = string_value[:target_length]
            except ValueError:
                msg = f"String length not a number: {target_length}, ignoring"
                log.error(msg)
        return string_value
    else:
        return value
