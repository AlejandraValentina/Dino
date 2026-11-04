"""Deterministic provenance for the bytes consumed by the Windows bundle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


def packaged_input_paths(root: Path) -> list[Path]:
    """Files copied, source-backed, or required to produce the shipped app."""
    root = Path(root)
    paths = {p for p in (root / "motorsim").rglob("*") if p.is_file()
             and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    paths.update(p for p in (root / "examples" / "projects").rglob("*") if p.is_file())
    paths.update(p for p in (root / "packaging").rglob("*")
                 if p.is_file() and (p.parent.name == "licenses" or p.name in {
                     "MotorSim.spec", "gui_entry.py", "dino_desktop_entry.py",
                     "worker_entry.py", "requirements-build.txt", "AVISOS.txt",
                     "INICIO-DINO.txt", "build_windows.py", "build_provenance.py",
                 }))
    required = {
        "packaging/MotorSim.spec", "packaging/gui_entry.py",
        "packaging/dino_desktop_entry.py", "packaging/worker_entry.py",
        "packaging/requirements-build.txt", "packaging/AVISOS.txt",
        "packaging/INICIO-DINO.txt", "packaging/build_windows.py",
        "packaging/build_provenance.py", "scripts/agents/storage_preflight.py",
        "results/2t-commercial-core-20261002/fixtures/v1-prime-mesh/fixture_a_prime-mesh-0.json",
    }
    paths.update(root / item for item in required)
    paths.update(p for p in (root / "packaging" / "licenses").rglob("*") if p.is_file())
    missing = sorted(p.relative_to(root).as_posix() for p in paths if not p.is_file())
    if missing:
        raise FileNotFoundError("Faltan entradas de build requeridas: " + ", ".join(missing))
    return sorted(paths, key=lambda p: p.relative_to(root).as_posix())


def input_manifest(root: Path) -> dict:
    root = Path(root)
    files = []
    for path in packaged_input_paths(root):
        data = path.read_bytes()
        files.append({"path": path.relative_to(root).as_posix(),
                      "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":")).encode("utf-8")
    return {"files": files, "sha256": hashlib.sha256(canonical).hexdigest()}


def git_status(root: Path, paths: list[str] | None = None) -> bytes:
    args = ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"]
    if paths:
        args += ["--", *paths]
    return subprocess.check_output(args, cwd=root)


def ensure_packaged_inputs_clean(root: Path) -> None:
    """Refuse a package if any app/build input differs from the named commit."""
    scope = ["motorsim", "packaging", "examples/projects",
             "scripts/agents/storage_preflight.py",
             "results/2t-commercial-core-20261002/fixtures/v1-prime-mesh/fixture_a_prime-mesh-0.json"]
    status = git_status(root, scope)
    if status:
        paths = []
        for entry in status.decode("utf-8", errors="replace").split("\0"):
            if len(entry) >= 4:
                paths.append(entry[3:])
        raise RuntimeError("Entradas del paquete/build con cambios locales; commit requerido: " +
                           ", ".join(paths[:12]))


def unrelated_dirty_fingerprint(root: Path) -> dict:
    """Summarize unrelated working-tree changes without recording local paths."""
    all_status = git_status(root)
    package_status = git_status(root, ["motorsim", "packaging", "examples/projects",
        "scripts/agents/storage_preflight.py",
        "results/2t-commercial-core-20261002/fixtures/v1-prime-mesh/fixture_a_prime-mesh-0.json"])
    unrelated = all_status  # Caller first requires package_status to be empty.
    if package_status:
        ensure_packaged_inputs_clean(root)
    entries = [item for item in unrelated.split(b"\0") if item]
    return {"source_dirty": bool(entries), "unrelated_dirty_entry_count": len(entries),
            "unrelated_dirty_status_sha256": hashlib.sha256(unrelated).hexdigest()}
