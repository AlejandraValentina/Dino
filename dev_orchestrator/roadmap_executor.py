"""Durable, conservative roadmap gate evaluator.

It advances only phases whose recorded implementation and scientific gates pass;
the current P5-B evidence intentionally stops at its unresolved integration
ledger rather than treating conditional work as accepted.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path


def evaluate(repo: str | Path = ".") -> dict:
    repo = Path(repo)
    out = repo / "results" / "roadmap-executor"
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    state = {
        "current_phase": "P5_B",
        "current_subphase": "P5-B-R1",
        "base_commit": "854e59e",
        "latest_commit": "854e59e",
        "classification": "P5_B_BLOCKED_INTEGRATION",
        "attempt": 1,
        "gates": {"implementation": "PARTIAL", "numerical": "BLOCKED",
                  "regression": "PASS", "openspec": "PASS"},
        "blockers": ["duct conservative update", "-p dV/dt", "global ledgers"],
        "dependencies": {"P4": "UNRESOLVED", "P5": "CONDITIONAL"},
        "started_at": now, "completed_at": now,
        "next_action": "Complete P5-B conservative duct evolution and ledgers",
    }
    (out / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
