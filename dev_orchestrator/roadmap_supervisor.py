"""Windows-safe outer supervisor for the durable roadmap executor."""
from __future__ import annotations
import json, os, shutil, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; R=ROOT/'results'/'roadmap-executor'
CFG=Path(__file__).with_name('roadmap_supervisor.json'); STATE=R/'supervisor_state.json'; LOCK=R/'supervisor.lock'
TERMINAL={'P9_VALIDATION_COMPLETED','P9_VALIDATION_PARTIAL','P9_BLOCKED_EXPERIMENTAL_DATA_REQUIRED','P9_BLOCKED_CONFIGURATION_MISMATCH','P9_BLOCKED_MODEL_DISCREPANCY'}

def now(): return datetime.now(timezone.utc).isoformat()
def read(p, default):
    try:return json.loads(Path(p).read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):return default
def write(p,obj):
    p=Path(p); tmp=p.with_suffix(p.suffix+'.tmp'); tmp.write_text(json.dumps(obj,indent=2),encoding='utf-8'); tmp.replace(p)
def git_head(): return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def git_status(): return subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).strip().splitlines()
def pid_alive(pid):
    if not pid: return False
    try:
        if os.name == 'nt':
            return subprocess.run(['tasklist','/FI',f'PID eq {int(pid)}'],capture_output=True,text=True).returncode == 0 and str(pid) in subprocess.run(['tasklist','/FI',f'PID eq {int(pid)}'],capture_output=True,text=True).stdout
        os.kill(int(pid),0); return True
    except BaseException: return False
def cli():
    c=read(CFG,{})
    if c.get('agent_command'): return c['agent_command']
    # Discovery is reported separately; no CLI is assumed to accept our
    # prompt protocol without an explicit command template.
    return None
def safe_status():
    s=read(R/'state.json',{}); q=read(R/'current_tasks.json',{'tasks':[]}); done=sum(x.get('status')=='DONE' for x in q.get('tasks',[]))
    sup=read(R/'supervisor_state.json',{})
    detected = [n for n in ('codex','opencode') if shutil.which(n)]
    status=sup.get('status','STOPPED')
    if status=='RUNNING' and not pid_alive(sup.get('pid')): status='STALE'
    hb=sup.get('last_heartbeat'); age=None
    return {'supervisor':status,'pid':sup.get('pid'),'pid_alive':pid_alive(sup.get('pid')),'child_pid':sup.get('child_pid'),'child_alive':pid_alive(sup.get('child_pid')),'HEAD':git_head(),'phase':s.get('current_phase'),'active_task':s.get('current_subphase'),'tasks':f'{done}/{len(q.get("tasks",[]))}','invocations':sup.get('invocation_count',0),'current_invocation':sup.get('current_invocation'),'last_heartbeat':hb,'detected_clis':detected,'terminal_reason':sup.get('terminal_reason')}
def acquire():
    if LOCK.exists():
        old=read(LOCK,{})
        if old.get('pid') and old['pid']!=os.getpid() and pid_alive(old['pid']): return False
    write(LOCK,{'pid':os.getpid(),'started_at':now(),'repo':str(ROOT),'HEAD':git_head()}); return True
def release():
    if LOCK.exists() and read(LOCK,{}).get('pid')==os.getpid(): LOCK.unlink()
def once():
    cmd=cli()
    if not cmd:return 'SUPERVISOR_READY_AGENT_COMMAND_REQUIRED'
    if not acquire(): return 'SUPERVISOR_BLOCKED_UNEXPECTED_WORKTREE'
    inv=uuid.uuid4().hex[:10]; d=R/'invocations'/inv; d.mkdir(parents=True,exist_ok=True)
    before={'invocation_id':inv,'timestamp':now(),'HEAD_before':git_head(),'phase_before':read(R/'state.json',{}).get('current_phase'),'active_task_before':read(R/'state.json',{}).get('current_subphase'),'working_tree_before':git_status()}; write(d/'before.json',before)
    prompt='Read AGENTS.md, roadmap state and current_tasks.json. Implement the active approved task completely, run focused tests, persist durable state. Do not reinterpret P4, do not push, preserve redme.txt unstaged.'
    (d/'prompt.txt').write_text(prompt,encoding='utf-8'); start=time.time(); timeout=read(CFG,{}).get('agent_timeout_seconds',3600)
    with open(d/'stdout.log','wb') as out, open(d/'stderr.log','wb') as err:
        p=subprocess.Popen(cmd,input=None,stdin=subprocess.PIPE,stdout=out,stderr=err,cwd=ROOT)
        write(STATE,{'status':'RUNNING','pid':os.getpid(),'child_pid':p.pid,'current_invocation':inv,'last_heartbeat':now(),'current_phase':before['phase_before'],'current_task':before['active_task_before']})
        p.stdin.write(prompt.encode('utf-8')); p.stdin.close(); started=time.time()
        while p.poll() is None:
            if time.time()-started > timeout:
                p.kill(); code='TIMEOUT'; break
            sup=read(STATE,{}); sup.update({'status':'RUNNING','pid':os.getpid(),'child_pid':p.pid,'current_invocation':inv,'last_heartbeat':now(),'HEAD':git_head()}); write(STATE,sup)
            time.sleep(read(CFG,{}).get('poll_seconds',2))
        else: code=p.returncode
    after={'HEAD_after':git_head(),'status_after':git_status(),'state_after':read(R/'state.json',{}),'tasks_after':read(R/'current_tasks.json',{})}; write(d/'result.json',{'returncode':code,'duration':time.time()-start,**after})
    previous=read(STATE,{}); count=int(previous.get('invocation_count',0))+1
    write(STATE,{'status':'RUNNING' if code==0 else 'BLOCKED','pid':os.getpid(),'child_pid':None,'started_at':previous.get('started_at',now()),'last_heartbeat':now(),'invocation_count':count,'current_invocation':inv,'current_phase':after['state_after'].get('current_phase'),'current_task':after['state_after'].get('current_subphase'),'HEAD':after['HEAD_after'],'terminal_reason':None if code==0 else 'AGENT_FAILED'})
    release(); return 'PASS' if code==0 else 'SUPERVISOR_AGENT_FAILED'
def main(argv):
    R.mkdir(parents=True,exist_ok=True); a=argv[1] if len(argv)>1 else 'status'
    if a=='status': print(json.dumps(safe_status(),indent=2)); return 0
    if a in ('once','resume'): print(once()); return 0
    if a=='stop': write(STATE,{'status':'STOP_REQUESTED','pid':os.getpid(),'last_heartbeat':now()}); print('STOP_REQUESTED'); return 0
    if a=='run':
        for _ in range(read(CFG,{}).get('max_invocations',20)):
            result=once(); print(result)
            if result!='PASS': return 0
        return 0
    if a=='start':
        log=open(R/'supervisor.log','a',encoding='utf-8')
        flags=getattr(subprocess,'CREATE_NEW_PROCESS_GROUP',0)|getattr(subprocess,'DETACHED_PROCESS',0)
        try: p=subprocess.Popen([sys.executable,str(Path(__file__)),'run'],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=flags,close_fds=False)
        except OSError: p=subprocess.Popen([sys.executable,str(Path(__file__)),'run'],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,close_fds=False)
        write(STATE,{'status':'RUNNING','pid':p.pid,'started_at':now(),'last_heartbeat':now(),'invocation_count':0,'current_invocation':None,'current_phase':read(R/'state.json',{}).get('current_phase'),'current_task':read(R/'state.json',{}).get('current_subphase'),'HEAD':git_head(),'terminal_reason':None})
        print(p.pid); return 0
    print('usage: status|run|resume|stop|once'); return 2
if __name__=='__main__': raise SystemExit(main(sys.argv))
