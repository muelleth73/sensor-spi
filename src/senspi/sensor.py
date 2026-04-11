"""
Transform raw sensor values to
"""

import logging

from senspi.constants import STRING_PARAMETERS
from senspi.transform import not_special

log = logging.getLogger(__name__)


def make_number_processor(parameters):
    previous_value = 1000.0
    offset = parameters.get("offset", 0.0)
    divisor = parameters.get("divisor", 1.0)
    assert abs(divisor) > 0.00000001
    multiplier = parameters.get("multiplier", 1.0)
    filter = parameters.get("filter", 0.05)
    assert filter >= 0.0 and filter <= 1.0
    log.debug(
        f"created number processor, offset={offset}, divisor={divisor}, multiplier={multiplier}, filter={filter}"
    )

    def number_processor(sender, value):
        nonlocal previous_value

        v = (value - offset) / divisor * multiplier
        address = parameters.get("address", None)
        if address is not None and abs(previous_value - v) > filter:
            # log.debug(f"sending {v} to {address}, prev={previous_value}")
            sender.send_message(address, v)
            previous_value = v

    return number_processor


def make_string_processor(parameters):
    previous_value = ""
    xfcase = STRING_PARAMETERS.get("case", None)
    xftrim = parameters.get("trim", None)
    log.debug(f"created string processor, case={xfcase}, trim={xftrim}")

    def string_processor(sender, value):
        nonlocal previous_value

        if xfcase == "upper":
            sval = value.upper()
        elif xfcase == "lower":
            sval = value.lower()
        else:
            sval = value
        if xftrim is not None:
            if xftrim < 1:
                log.warning(f"trim value too low: {xftrim}, ignoring")
            else:
                sval = sval[:xftrim]
        address = parameters.get("address", None)
        if address is not None and sval != previous_value:
            sender.send_message(address, sval)
            previous_value = sval

    return string_processor


def make_processor(parameters):
    """
    Create a function that will transform its input value
    according to the parameters provided and then send
    it to the address specified in the parameters.

    For paths that are present in the value, but not in
    the parameters, the schema provides defaults.

    The generated function will accept a
    value expected to conform to the structure of described
    by the `SCHEMA` attribute of the corresponding sensor module
    and a python-osc UDPClient object
    to send the value to.

    The generated function will not return anything.
    """

    typ = parameters.get("@type", None)
    if typ == "map":
        items = {}
        for k, v in filter(not_special, parameters.items()):
            items[k] = make_processor(v)
        items["@type"] = "map"
        return items
    elif typ == "array":
        element_type = parameters.get("@items", None)
        element = make_processor(element_type)
        return {"@type": "array", "@items": element}
    elif typ == "tuple":
        items = []
        para_idx = 0
        for element_type in parameters.get("@items", []):
            items.append(make_processor(element_type))
            para_idx += 1
        return {"@type": "tuple", "@items": items}
    elif typ == "float":
        return {
            "@type": typ,
            "@processor": make_number_processor(parameters.get("@parameters", {})),
        }
    elif typ == "string":
        return {
            "@type": typ,
            "@processor": make_string_processor(parameters.get("@parameters", {})),
        }
    else:
        log.error(f"make_number_processor error: Unknown @type '{typ}' in {parameters}")


def process(processor, sender, value):
    typ = processor.get("@type", None)
    if typ == "map":
        for k, v in filter(not_special, processor.items()):
            item_value = value.get(k, None)
            if item_value is not None:
                process(v, sender, item_value)
    elif typ == "array":
        assert isinstance(value, list)
        element_type = processor.get("@items", None)
        for v in value:
            process(element_type, sender, v)
    elif typ == "tuple":
        assert isinstance(value, list)
        para_idx = 0
        element_types = processor.get("@items", [])
        assert len(element_types) == len(value)
        for element_type in element_types:
            process(element_type, sender, value[para_idx])
            para_idx += 1
    elif typ == "float" or typ == "string":
        processing_function = processor.get("@processor", None)
        # log.debug(f"processing: sending {value} to {sender} using function {processing_function}")
        processing_function(sender, value)
    else:
        log.error(f"processing error: Unknown @type '{typ}' in {processor}")
