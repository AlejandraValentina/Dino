import json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_status():
 r=subprocess.run([sys.executable,'dev_orchestrator/roadmap_supervisor.py','status'],cwd=ROOT,capture_output=True,text=True)
 assert r.returncode==0 and 'P5_B' in r.stdout
def test_missing_agent_command():
 r=subprocess.run([sys.executable,'dev_orchestrator/roadmap_supervisor.py','once'],cwd=ROOT,capture_output=True,text=True)
 assert 'SUPERVISOR_READY_AGENT_COMMAND_REQUIRED' in r.stdout
