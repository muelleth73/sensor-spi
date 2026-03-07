from pathlib import Path

import pytest

import senspi.mock.composite_readout as composite_faker
import senspi.mock.constant_number_readout as num_faker
import senspi.mock.constant_string_readout as str_faker
import senspi.readconfig as cfg
import senspi.transform as xf


@pytest.fixture
def config_fxt() -> xf.SchemaType:
    config = cfg.get_config(Path("./config/config-test.yaml"))
    return config


@pytest.fixture
def sensors_fxt(config_fxt) -> xf.SchemaType:
    return config_fxt["sensors"]


@pytest.fixture
def transform_fxt(sensors_fxt) -> xf.SchemaType:
    return sensors_fxt["fake_composite"]["transform"]


@pytest.fixture
def num_param_fxt(transform_fxt) -> xf.SchemaType:
    return {
        "params": transform_fxt["temperature"],
        "schema": num_faker.SCHEMA,
    }


@pytest.fixture
def str_param_fxt(transform_fxt) -> xf.SchemaType:
    return {
        "params": transform_fxt["atmosphere"][1],
        "schema": str_faker.SCHEMA,
    }


@pytest.fixture
def composite_param_fxt(transform_fxt) -> xf.SchemaType:
    return {
        "params": transform_fxt,
        "schema": composite_faker.SCHEMA,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_make_string_value():
    v = composite_faker.make_value(str_faker.SCHEMA)
    assert isinstance(v, str)
    assert v == str_faker.VALUE


def test_make_float_value():
    v = composite_faker.make_value(num_faker.SCHEMA)
    assert isinstance(v, float)
    assert v == num_faker.VALUE


def test_make_composite_value():
    v = composite_faker.make_value(composite_faker.SCHEMA)
    assert isinstance(v, dict)
    items = dict(filter(xf.not_special, composite_faker.SCHEMA.items()))
    assert set(v) == set(items)
    temp = v.get("temperature", None)
    assert temp is not None
    assert isinstance(temp, float)
    assert temp == num_faker.VALUE
    giro = v.get("giroscope", None)
    assert giro is not None
    assert isinstance(giro, list)
    assert len(giro) == 3
    assert giro[0] == num_faker.VALUE
    atmo = v.get("atmosphere", None)
    assert atmo is not None
    assert isinstance(atmo, list)
    assert len(atmo) == 2
    accel = v.get("acceleration", None)
    assert accel is not None
    assert isinstance(accel, dict)
    assert len(accel) == 3


def test_walk(transform_fxt):
    params = transform_fxt
    v = composite_faker.make_value(composite_faker.SCHEMA)
    items = []
    for i in xf.walk([], v, params):
        items.append(i)

    assert len(items) == 9
    temp = items[8]
    assert temp[0] == ["temperature"]
    param = temp[2]
    assert isinstance(param, dict)
    assert "@parameters" in param


def test_merge_number_param_no_schema(num_param_fxt):
    p = num_param_fxt["params"]
    s = num_faker.NO_DEFAULTS_SCHEMA

    params = xf.add_defaults(s, p)
    assert isinstance(params, dict)
    assert "@type" in params
    assert "@parameters" in params
    ptype = params.get("@type", None)
    assert ptype is not None
    assert ptype == "float"
    p = params["@parameters"]
    assert len(p) == 2
    assert p["offset"] == 278.1
    assert p["address"] == "/param/temperature"


def test_merge_number_param_with_schema(num_param_fxt):
    p = num_param_fxt["params"]
    s = num_param_fxt["schema"]
    params = xf.add_defaults(s, p)
    assert isinstance(params, dict)
    assert "@type" in params
    assert "@parameters" in params
    assert params["@type"] == "float"
    p = params["@parameters"]
    assert len(p) == 5
    assert p["filter"] == 0.05
    assert p["address"] == "/param/temperature"


def test_merge_string_param(str_param_fxt):
    p = str_param_fxt["params"]
    s = str_param_fxt["schema"]
    params = xf.add_defaults(s, p)
    assert isinstance(params, dict)
    assert "@type" in params
    assert "@parameters" in params
    assert params["@type"] == "string"
    p = params["@parameters"]
    assert len(p) == 3
    assert p["case"] == "upper"
    assert p["trim"] == 4


def test_merge_composite_param(composite_param_fxt):
    p = composite_param_fxt["params"]
    s = composite_param_fxt["schema"]
    params = xf.add_defaults(s, p)
    assert isinstance(params, dict)
    assert "@type" in params
    assert params["@type"] == "map"
    assert len(params) == 5
    zparms = params.get("acceleration", {}).get("z", {}).get("@parameters", {})
    assert zparms
    assert zparms["multiplier"] == pytest.approx(2.0)  # set in config
    assert zparms["offset"] == pytest.approx(0.0)  # default
    sparms = params.get("atmosphere", {}).get("@items", [])
    assert isinstance(sparms, list)
    assert len(sparms) == 2
    assert sparms[1]["@parameters"]["case"] == "upper"
    assert sparms[1]["@parameters"]["trim"] == 4
    gparms = params.get("giroscope", {}).get("@items", [])
    assert isinstance(gparms, dict)
    assert gparms["@parameters"]["offset"] == pytest.approx(1000.0)


def test_transform_float(num_param_fxt):
    params = num_param_fxt["params"]
    v = num_faker.VALUE
    t = xf.transform(v, params)
    assert isinstance(t, float)
    assert t == pytest.approx((num_faker.VALUE - 278.1), 0.001)


def test_transform_string(str_param_fxt):
    params = str_param_fxt["params"]
    v = str_faker.VALUE
    t = xf.transform(v, params)
    assert isinstance(t, str)
    assert t == "TEST"


def test_transform_composite(transform_fxt):
    params = transform_fxt
    v = composite_faker.make_value(composite_faker.SCHEMA)
    t = xf.transform(v, params)
    assert isinstance(t, dict)
    accl = t.get("acceleration", None)
    assert isinstance(accl, dict)
    z = accl.get("z", 0.0)
    assert z == pytest.approx(num_faker.VALUE * 2.0)
    git = t.get("giroscope", None)
    assert isinstance(git, list)
    assert git[2] == pytest.approx((num_faker.VALUE - 1000) / 10)
    atmo = t.get("atmosphere", None)
    assert isinstance(atmo, list)
    assert atmo[0] == pytest.approx(num_faker.VALUE / 5)
    assert atmo[1] == "TEST"
