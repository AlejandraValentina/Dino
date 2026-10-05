import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PRODUCER = ROOT / "scripts" / "produce_integrated_cycle_evidence.py"


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
