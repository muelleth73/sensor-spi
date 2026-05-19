from pathlib import Path

import pytest

import senspi.mock.composite_readout as composite_faker
import senspi.readconfig as cfg
import senspi.sensor as sens
import senspi.transform as xf
from senspi.mock.udp_client import MockUDPClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def osc_client_fxt():
    c = MockUDPClient()
    return c


@pytest.fixture
def config_fxt() -> xf.SchemaType:
    config = cfg.get_config(Path("./config/config-test.yaml"))
    return config


@pytest.fixture
def composite_param_fxt(config_fxt) -> xf.SchemaType:
    return {
        "params": config_fxt["sensors"]["fake_composite"]["transform"],
        "schema": composite_faker.SCHEMA,
    }


@pytest.fixture
def composite_proc_builder_fxt(composite_param_fxt) -> xf.ParameterType:
    p = composite_param_fxt["params"]
    s = composite_param_fxt["schema"]
    return xf.add_defaults(s, p)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_make_composite_processor(composite_proc_builder_fxt):
    proc = sens.make_processor(composite_proc_builder_fxt)
    print(proc)
    assert 5 == len(proc)
    assert "atmosphere" in proc
    atm = proc["atmosphere"]
    assert "@items" in atm


def test_process_composite(composite_proc_builder_fxt, osc_client_fxt):
    proc = sens.make_processor(composite_proc_builder_fxt)
    value = composite_faker.make_value(composite_faker.SCHEMA)
    sender = osc_client_fxt
    sens.process(proc, sender, value)
    hist = sender.get_history()
    assert 5 == len(hist)
    assert "test" == hist[3][1]
