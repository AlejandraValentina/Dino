import json
import hashlib
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "scripts" / "produce_integrated_cycle_evidence.py"
sys.path.insert(0, str(ROOT / "scripts"))
import produce_integrated_cycle_evidence as producer


def test_committed_synthetic_fixture_configs_load_from_outside_repository(tmp_path):
    for fixture_id in ("A", "B"):
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
