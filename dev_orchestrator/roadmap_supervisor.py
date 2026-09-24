"""Durable, Windows-safe supervisor for the roadmap executor."""
from __future__ import annotations

import json, os, shutil, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results" / "roadmap-executor"
CFG = Path(__file__).with_name("roadmap_supervisor.json")
STATE = R / "supervisor_state.json"
LOCK = R / "supervisor.lock"
STOP_REQUEST = R / "supervisor.stop"
DEFAULT_LIVE_STATUS = R / "LIVE_STATUS.md"


def now(): return datetime.now(timezone.utc).isoformat()
def local_now(): return datetime.now().astimezone().isoformat()


def read(path, default):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError): return default


def write(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def cfg(): return read(CFG, {})
def live_path():
    path = Path(cfg().get("live_status_file") or DEFAULT_LIVE_STATUS)
    return path if path.is_absolute() else ROOT / path


def git_head():
    try: return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError): return "UNKNOWN"


def git_status():
    try: return subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).splitlines()
    except (OSError, subprocess.CalledProcessError): return []


def _meaningful_status(lines):
    runtime = str(R.relative_to(ROOT)).replace("\\", "/") + "/"
    return sorted(line for line in lines if runtime not in line.replace("\\", "/"))


def pid_alive(pid):
    if not pid: return False
    try:
        pid = int(pid)
        if os.name == "nt":
            result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, check=False)
            return result.returncode == 0 and any(str(pid) in line.split() for line in result.stdout.splitlines())
        os.kill(pid, 0); return True
    except (ValueError, OSError, subprocess.SubprocessError): return False


def cli():
    command = cfg().get("agent_command")
    return list(command) if command else None


def _roadmap_snapshot():
    state = read(R / "state.json", {})
    doc = read(R / "current_tasks.json", {"tasks": []})
    tasks = doc.get("tasks", [])
    return {"HEAD": git_head(), "active_task": state.get("current_subphase") or doc.get("active_task"),
            "done": sum(t.get("status") == "DONE" for t in tasks), "total": len(tasks),
            "phase": state.get("current_phase") or doc.get("phase"), "blockers": state.get("blockers", []),
            "worktree": _meaningful_status(git_status())}


def _progressed(before, after):
    return any(before.get(k) != after.get(k) for k in ("HEAD", "active_task", "done", "phase", "blockers", "worktree"))


def _tail(path, count=12):
    try: data = Path(path).read_bytes().decode("utf-8", errors="replace")
    except OSError: return ["(stdout.log unavailable)"]
    lines = [line.rstrip() for line in data.splitlines() if line.strip()]
    return lines[-count:] or ["(stdout.log is empty)"]


def _heartbeat_age(value):
    if not value: return "unknown"
    try: return f"{max(0.0, time.time() - datetime.fromisoformat(value).timestamp()):.1f}s"
    except ValueError: return "unknown"


def _elapsed(state):
    try: return f"{max(0.0, time.time() - float(state.get('agent_started_at'))):.1f}s" if state.get("agent_started_at") else "0.0s"
    except (TypeError, ValueError): return "unknown"


def _live_markdown(state):
    invocation = state.get("current_invocation")
    stdout = R / "invocations" / str(invocation) / "stdout.log" if invocation else None
    child = state.get("child_pid")
    child_text = f"{child} ({'alive' if pid_alive(child) else 'not alive'})" if child else "none"
    supervisor_text = f"{state.get('pid', 'none')} ({'alive' if pid_alive(state.get('pid')) else 'not alive'})"
    return "\n".join([
        "# MotorSim roadmap supervisor live status", "", f"- Current UTC: {now()}",
        f"- Current local: {local_now()}", f"- Supervisor: {state.get('status', 'STOPPED')} / PID {supervisor_text}",
        f"- Heartbeat age: {_heartbeat_age(state.get('last_heartbeat'))}", f"- Child PID: {child_text}",
        f"- Phase/task: {state.get('current_phase') or 'unknown'} / {state.get('current_task') or 'unknown'}",
        f"- DONE/total: {state.get('done', '?')}/{state.get('total', '?')}",
        f"- Invocation: {invocation or 'none'} (count {state.get('invocation_count', 0)})",
        f"- Elapsed agent time: {_elapsed(state)}", f"- HEAD: {state.get('HEAD') or git_head()}",
        f"- No-progress count: {state.get('no_progress_count', 0)}",
        f"- Terminal reason: {state.get('terminal_reason') or 'none'}", "",
        "## Current Codex stdout (last readable lines)", "", "```text", *(_tail(stdout) if stdout else ["(no active invocation)"]), "```", ""
    ])


def publish_live(state=None):
    state = dict(read(STATE, {}), **(state or {})); path = live_path(); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp"); tmp.write_text(_live_markdown(state), encoding="utf-8"); tmp.replace(path)


def _save(state):
    state["last_heartbeat"] = now(); write(STATE, state); publish_live(state)


def _lock_owner(): return read(LOCK, {})


def acquire():
    R.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        old = _lock_owner(); old_pid = old.get("pid")
        try: other_live = old_pid and int(old_pid) != os.getpid() and pid_alive(old_pid)
        except (TypeError, ValueError): other_live = False
        if other_live: return False
        try: LOCK.unlink()
        except FileNotFoundError: pass
    try: fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError: return False
    with os.fdopen(fd, "w", encoding="utf-8") as handle: json.dump({"pid": os.getpid(), "started_at": now(), "repo": str(ROOT)}, handle)
    return True


def release():
    if LOCK.exists() and _lock_owner().get("pid") == os.getpid(): LOCK.unlink()


def _prompt(snapshot):
    tasks = read(R / "current_tasks.json", {"tasks": []}).get("tasks", [])
    active_id = str(snapshot.get("active_task") or "").split()[0]
    task = next((item for item in tasks if item.get("id") == active_id), {})
    same_phase = [item for item in tasks if item.get("phase") == task.get("phase")]
    final_hint = ""
    if task and all(item.get("status") == "DONE" for item in same_phase if item.get("id") != task.get("id")):
        final_hint = " If this is the final task of the phase, advance only to the next already-approved roadmap phase/task queue when repository specs/governance define it; never invent a scientific contract. A real contract ambiguity is a blocker."
    return (f"Read AGENTS.md, current_tasks.json and state.json. The exact active task is {task.get('id', active_id)} — "
            f"{task.get('description', snapshot.get('active_task'))} in phase {snapshot.get('phase')}. Implement now. "
            "Run focused tests, persist evidence/queue/state, and commit a local checkpoint if appropriate. Do not push. "
            "Preserve redme.txt deleted and unstaged. P4 remains unresolved and NOT_GRANTED." + final_hint)


def _invoke():
    command = cli()
    if not command: return "SUPERVISOR_READY_AGENT_COMMAND_REQUIRED"
    before = _roadmap_snapshot(); inv = uuid.uuid4().hex[:10]; directory = R / "invocations" / inv; directory.mkdir(parents=True, exist_ok=True)
    write(directory / "before.json", {"invocation_id": inv, "timestamp": now(), **before})
    (directory / "prompt.txt").write_text(_prompt(before), encoding="utf-8")
    state = dict(read(STATE, {})); state.update({"status": "RUNNING", "pid": os.getpid(), "child_pid": None, "current_invocation": inv,
        "current_phase": before["phase"], "current_task": before["active_task"], "done": before["done"], "total": before["total"],
        "HEAD": before["HEAD"], "agent_started_at": time.time(), "terminal_reason": None})
    with open(directory / "stdout.log", "wb") as out, open(directory / "stderr.log", "wb") as err:
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err, cwd=ROOT); state["child_pid"] = child.pid; _save(state)
        try:
            child.stdin.write(_prompt(before).encode("utf-8")); child.stdin.close()
        except (BrokenPipeError, OSError):
            # A short-lived fake/agent may exit before consuming its prompt.
            # Its exact return code is still collected below.
            try: child.stdin.close()
            except OSError: pass
        started = time.time(); code = None
        while child.poll() is None:
            if STOP_REQUEST.exists(): child.terminate(); code = "STOP_REQUESTED"; break
            if time.time() - started > float(cfg().get("agent_timeout_seconds", 3600)): child.kill(); code = "TIMEOUT"; break
            state["HEAD"] = git_head(); _save(state); time.sleep(float(cfg().get("poll_seconds", 2)))
        if code is None: code = child.returncode
    after = _roadmap_snapshot(); write(directory / "result.json", {"returncode": code, "duration": time.time() - started,
        "progress": _progressed(before, after), "before": before, "after": after})
    return code, before, after, inv


def _finish(result):
    code, before, after, inv = result; state = dict(read(STATE, {})); progress = _progressed(before, after)
    no_progress = 0 if progress else int(state.get("no_progress_count", 0)) + 1
    state.update({"child_pid": None, "invocation_count": int(state.get("invocation_count", 0)) + 1, "current_invocation": inv,
        "current_phase": after["phase"], "current_task": after["active_task"], "done": after["done"], "total": after["total"],
        "HEAD": after["HEAD"], "no_progress_count": no_progress, "agent_started_at": None})
    return state, code, progress, no_progress


def _run_loop():
    if not acquire(): return "SUPERVISOR_BLOCKED_ALREADY_RUNNING"
    initial = _roadmap_snapshot(); state = dict(read(STATE, {})); state.update({"status": "RUNNING", "pid": os.getpid(), "child_pid": None,
        "started_at": state.get("started_at", now()), "current_phase": initial["phase"], "current_task": initial["active_task"],
        "done": initial["done"], "total": initial["total"], "HEAD": initial["HEAD"], "terminal_reason": None}); _save(state)
    try:
        while True:
            if STOP_REQUEST.exists(): state.update({"status": "STOPPED", "terminal_reason": "SUPERVISOR_STOP_REQUESTED"}); _save(state); return state["terminal_reason"]
            limit = int(cfg().get("max_invocations", 0))
            if limit > 0 and int(state.get("invocation_count", 0)) >= limit:
                state.update({"status": "BLOCKED", "terminal_reason": "SUPERVISOR_BLOCKED_INVOCATION_LIMIT"}); _save(state); return state["terminal_reason"]
            result = _invoke()
            if isinstance(result, str): state.update({"status": "BLOCKED", "terminal_reason": result}); _save(state); return result
            state, code, progress, no_progress = _finish(result)
            if STOP_REQUEST.exists(): state.update({"status": "STOPPED", "terminal_reason": "SUPERVISOR_STOP_REQUESTED"}); _save(state); return state["terminal_reason"]
            if no_progress > int(cfg().get("max_no_progress_attempts", 3)):
                state.update({"status": "BLOCKED", "terminal_reason": "SUPERVISOR_BLOCKED_NO_PROGRESS"}); _save(state); return state["terminal_reason"]
            if code != 0 and not progress:
                state.update({"status": "BLOCKED", "terminal_reason": "SUPERVISOR_AGENT_FAILED"}); _save(state); return state["terminal_reason"]
            state.update({"status": "RUNNING", "terminal_reason": None}); _save(state)
    finally: release()


def safe_status():
    state = read(STATE, {}); snap = _roadmap_snapshot(); status = state.get("status", "STOPPED")
    if status == "RUNNING" and not pid_alive(state.get("pid")): status = "STALE"
    return {"supervisor": status, "pid": state.get("pid"), "pid_alive": pid_alive(state.get("pid")), "child_pid": state.get("child_pid"),
        "child_alive": pid_alive(state.get("child_pid")), "heartbeat_age": _heartbeat_age(state.get("last_heartbeat")), "HEAD": snap["HEAD"],
        "phase": snap["phase"], "active_task": snap["active_task"], "tasks": f'{snap["done"]}/{snap["total"]}',
        "invocations": state.get("invocation_count", 0), "no_progress_count": state.get("no_progress_count", 0),
        "current_invocation": state.get("current_invocation"), "last_heartbeat": state.get("last_heartbeat"),
        "detected_clis": [n for n in ("codex", "opencode") if shutil.which(n)], "terminal_reason": state.get("terminal_reason")}


def _show():
    path = live_path().resolve(); code = shutil.which("code")
    if code:
        try: subprocess.Popen([code, "--reuse-window", str(path)], cwd=ROOT)
        except OSError: pass
    print(path); return 0


def main(argv):
    R.mkdir(parents=True, exist_ok=True); command = argv[1] if len(argv) > 1 else "status"
    if command == "status": print(json.dumps(safe_status(), indent=2)); return 0
    if command == "show": return _show()
    if command == "stop": write(STOP_REQUEST, {"requested_at": now(), "requested_by": os.getpid()}); print("STOP_REQUESTED"); return 0
    if command == "once":
        if not acquire(): print("SUPERVISOR_BLOCKED_ALREADY_RUNNING"); return 1
        try:
            result = _invoke()
            if isinstance(result, str): print(result); return 0
            state, code, progress, _ = _finish(result); state["status"] = "STOPPED"; _save(state); print("PASS" if code == 0 else "SUPERVISOR_AGENT_FAILED"); return 0 if code == 0 else 1
        finally: release()
    if command in ("run", "resume"): print(_run_loop()); return 0
    if command == "start":
        log = open(R / "supervisor.log", "a", encoding="utf-8"); flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
        try: process = subprocess.Popen([sys.executable, str(Path(__file__)), "run"], cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log, creationflags=flags, close_fds=False)
        except OSError: process = subprocess.Popen([sys.executable, str(Path(__file__)), "run"], cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log, close_fds=False)
        log.close(); print(process.pid); _show(); return 0
    print("usage: status|show|run|resume|once|start|stop"); return 2


if __name__ == "__main__": raise SystemExit(main(sys.argv))
