import json
import hashlib
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "scripts" / "produce_integrated_cycle_evidence.py"
sys.path.insert(0, str(ROOT / "scripts"))
import produce_integrated_cycle_evidence as producer


def test_committed_synthetic_fixture_configs_load_from_outside_repository(tmp_path):
    for fixture_id in ("A", "B", "C"):
        result = subprocess.run(
            [sys.executable, str(PRODUCER), "--fixture", fixture_id,
             "--validate-only"],
            cwd=tmp_path, check=True, capture_output=True, text=True)
        output = json.loads(result.stdout)
        assert output["fixture_id"] == fixture_id
        assert output["configuration_schema"] == (
            "MOTORSIM_INTEGRATED_ENGINE_2T_CONFIG_V2")
        assert len(output["engine_configuration_sha256"]) == 64
        assert output["fixture_status"] == (
            "AUDIT_REMEDIATION_FIXTURE" if fixture_id == "C" else
            "HISTORICAL_SUPERSEDED_BY_POSTHOC_AUDIT")


def test_producer_refuses_to_integrate_without_preregistration(tmp_path):
    output = tmp_path / "should-not-be-created"
    result = subprocess.run(
        [sys.executable, str(PRODUCER), "--fixture", "A", "--horizon", "2",
         "--restart-cycle", "1", "--output", str(output)],
        cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 2
    assert "integration requires" in result.stderr
    assert not output.exists()


def test_preregistration_hash_is_independent_of_json_line_endings():
    document = {"schema": "AUDIT_FIXTURE", "cycle": 20, "title": "Fixture A"}
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"),
                           allow_nan=False).encode("utf-8")
    lf = (json.dumps(document, sort_keys=True, indent=2) + "\n").encode("utf-8")
    crlf_bom = b"\xef\xbb\xbf" + lf.replace(b"\n", b"\r\n")

    left = producer._decode_json_document(lf)
    right = producer._decode_json_document(crlf_bom)
    left_hash = hashlib.sha256(producer._canonical_bytes(left)).hexdigest()
    right_hash = hashlib.sha256(producer._canonical_bytes(right)).hexdigest()
    assert left == right == document
    assert left_hash == right_hash


def test_failure_receipt_preserves_cause_partial_state_and_retry_history(tmp_path):
    rejected = [{"angle_deg": 107.65, "attempted_step_deg": 0.5,
                 "reason": "inadmissible species mass"}]
    engine = SimpleNamespace(
        crank_angle_unwrapped_deg=107.65, accepted_steps=240,
        state={"chambers": {"cylinder": [1.0, 0.0, 100.0]}},
        inventory=lambda: {"mass_kg": 1.0},
        ledger={"external_mass_kg": 0.0})

    producer._write_failure_receipt(
        tmp_path, "C", 1, 360.0, engine, "config-sha", "prereg-sha",
        rejected, ValueError("no accepted step at 107.65 degrees"))

    receipt = json.loads((tmp_path / "failure.json").read_text(encoding="utf-8"))
    assert receipt["schema"] == "MOTORSIM_COMMERCIAL_CYCLE_FAILURE_V1"
    assert receipt["reached_angle_deg"] == 107.65
    assert receipt["failure_reason"] == "no accepted step at 107.65 degrees"
    assert receipt["current_state"] == engine.state
    assert receipt["rejected_trials"] == rejected
