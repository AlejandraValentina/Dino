import math

import pytest

from motorsim.engineering_outputs import (
    build_engineering_output,
    validate_engineering_output,
)


def output(**changes):
    values = dict(
        rpm=6000.0, cycle_number=3,
        angles_deg=(180.0, 270.0, 360.0, 450.0, 540.0),
        channels={
            "cylinder_pressure_pa": {"values": [100_000, 150_000, 200_000, 150_000, 100_000],
                                     "source": "P5C primary trajectory"},
            "exhaust_mach": {"values": [0, .2, .4, .2, 0], "source": "P4 duct trace"},
        },
        cycle_metrics={
            "indicated_work_j": {"value": 42.0, "status": "DEFINED",
                                 "reason": None, "source": "P8 cycle integrator"},
            "bsfc_g_kwh": {"value": None, "status": "UNDEFINED",
                           "reason": "NONPOSITIVE_BRAKE_POWER", "source": "fuel ledger"},
        },
        dependency_status="CONDITIONAL_ON_P4",
    )
    values.update(changes)
    return build_engineering_output(**values)


def test_schema_carries_units_provenance_and_explicit_nonclaims():
    record = output()
    assert record["schema"] == "MOTORSIM_ENGINEERING_OUTPUTS_V1"
    assert record["operating_point"]["cycle_convention"] == "2T_360_DEG_ONE_CYCLE_PER_REV"
    assert record["operating_point"]["dependency_status"] == "CONDITIONAL_ON_P4"
    assert record["crank_angle_trace"]["channels"]["cylinder_pressure_pa"]["unit"] == "Pa"
    assert record["crank_angle_trace"]["channels"]["cylinder_pressure_pa"]["source"] == "P5C primary trajectory"
    assert record["cycle_metrics"]["bsfc_g_kwh"]["status"] == "UNDEFINED"
    assert record["claims"] == {"periodicity": "NOT_EVALUATED",
        "experimental_validation": "NOT_PERFORMED", "predictive_validation": "NOT_CLAIMED"}
    assert validate_engineering_output(record) == record


@pytest.mark.parametrize("change", [
    {"angles_deg": (0, 90, 180)},
    {"rpm": True}, {"cycle_number": 0},
    {"channels": {"fabricated_curve": {"values": [1, 2, 3, 4, 5], "source": "x"}}},
    {"channels": {"cylinder_pressure_pa": {"values": [1, 2], "source": "x"}}},
    {"channels": {"cylinder_pressure_pa": {"values": [1, 2, math.nan, 4, 5], "source": "x"}}},
    {"dependency_status": "P4_PASS"},
])
def test_bad_trace_or_operating_point_is_rejected(change):
    with pytest.raises(ValueError):
        output(**change)


def test_malformed_undefined_metric_and_modified_units_are_rejected():
    bad = output()
    bad["cycle_metrics"]["bsfc_g_kwh"]["reason"] = None
    with pytest.raises(ValueError):
        validate_engineering_output(bad)
    bad = output()
    bad["crank_angle_trace"]["channels"]["cylinder_pressure_pa"]["unit"] = "bar"
    with pytest.raises(ValueError):
        validate_engineering_output(bad)


def test_schema_never_claims_four_stroke_or_nonperiodic_trace_as_2t():
    with pytest.raises(ValueError):
        output(cycle_period_deg=720.0)
