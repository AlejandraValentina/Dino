"""Cierre P0 con revisión independiente aportada explícitamente; no ejecuta campañas.

python -m dev_orchestrator.p0_finalize <run-dir> --review <review-envelope.json>
Conserva evidencia inicial y verifica vínculo SHA256, artefactos y scope Git.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
from .contracts import read_json,validate_named,load_phase,inside
from .git_state import snapshot,compare
from .evidence.build_report import build_report,artifacts
from .gates.evaluate import evaluate
from .p0_campaign import ROOT,sha,main_gate,MAIN_RPMS,production_hashes
from motorsim.prototype import write_json


def validate_review(envelope,evidence_path):
    data=validate_named(read_json(evidence_path),'evidence')
    if data['phase_id']!='P0' or envelope['run_id']!=data['run_id'] or envelope['evidence_sha256']!=sha(evidence_path):
        raise ValueError('Revisión no vinculada a esta evidencia P0')
    review=validate_named(envelope['review'],'review')
    if review['kind']!='independent': raise ValueError('P0 requiere revisión independiente real')
    return data,review


def final_label(data,campaign):
    if data['scope_violations']: return 'BLOCKED_SCOPE_VIOLATION'
    if data['gate']=='FAILED_INFRASTRUCTURE': return 'P0_FAILED_INFRASTRUCTURE'
    scientific=main_gate(campaign['rows'],campaign['regressions'])
    if scientific!='ELIGIBLE_FOR_REVIEW_AND_FREEZE': return scientific
    if data['gate']=='SCIENTIFIC_CHANGE_REQUIRED': return data['gate']
    return 'P0_PASS_BASELINE_FROZEN' if data['gate']=='PASS' else 'BLOCKED_REVIEW_OR_EVIDENCE'


def preflight_destinations(destination,names):
    if any((destination/n).exists() for n in names):
        raise FileExistsError('Baseline existente: no sobrescribir')


def preserve(path,content):
    # Reintentar un cierre interrumpido no reemplaza su evidencia original.
    if path.exists():
        if path.read_bytes()!=content: raise ValueError('Evidencia previa distinta: '+str(path))
    else:
        with path.open('xb') as stream: stream.write(content)


def rollback_close(run_dir,created):
    for path in created:
        # No descartar una modificación concurrente, incluso de un archivo nuevo.
        if path.exists() and path.read_bytes()==(run_dir/'artifacts'/path.name).read_bytes(): path.unlink()
    for name in ('evidence.json','summary.md'):
        (run_dir/name).write_bytes((run_dir/'artifacts'/('pre-review-'+name)).read_bytes())


def baseline_document(campaign):
    return dict(status='NUMERICALLY_VERIFIED_BASELINE',human_acceptance='WAITING_HUMAN_APPROVAL',
        solver_source_commit=campaign['git_commit'],model=campaign['model'],case=campaign['case'],
        profile=campaign['profile'],regularization_Pa=campaign['regularization_Pa'],
        minimum_half_step_deg=campaign['minimum_half_step_deg'],public_domains=campaign['public_domains'],
        production_sha256=campaign['source_sha256'],campaign_run_id=campaign['run_id'],
        main=campaign['rows'],historical_regression=campaign['regressions'],stress=campaign['stress'],
        stress_state=campaign['stress_state'],statistics_main=campaign['statistics_main'],
        statistics_all=campaign['statistics_all'],wall_total=campaign['wall_total'],
        interpretation='Malla2500:500:15000 acreditada numéricamente; no prueba de cada RPM real intermedio. Modelo0D sin ondas, sin escape sintonizado predictivo, sin validación experimental.',
        limitations=['<2250 rpm no acreditado;2250 observado PASS; límite público conservador2500.',
            'Mecanismos de baja RPM diagnosticados, fuera del cierre P0.',
            'Conservative stage species limiter evaluated and rejected; production solver unchanged.',
            'P1–P9 deshabilitadas; no autorización 1D ni ampliación pública.'])


def finalize(run_dir,review_path):
    run_dir=run_dir.resolve()
    if run_dir.parent!=ROOT/'dev_orchestrator/runs': raise ValueError('Usar el run original, no copia de evidencia')
    if (run_dir/'artifacts/p0-finalized.json').exists(): raise ValueError('P0 ya finalizado; no sobrescribir')
    envelope=read_json(review_path); data,review=validate_review(envelope,run_dir/'evidence.json')
    phase=load_phase(ROOT,'P0',read_json(ROOT/'dev_orchestrator/config.json'))[1]
    campaign=read_json(run_dir/'artifacts/campaign.json')
    inventory=read_json(run_dir/'artifacts/inventory.json')
    intact=all(sha(inside(run_dir,name))==value for name,value in inventory.items())
    intact &= all(sha(inside(run_dir,r['path']))==r['sha256'] for r in data['artifacts'])
    intact &= campaign['source_sha256']==production_hashes()
    before=read_json(run_dir/'artifacts/git-before.json')
    changed,violations,touched=compare(before,snapshot(ROOT),phase)
    data['files_changed']=changed;data['scope_violations']=sorted(set(data['scope_violations']+violations));data['preexisting_touched']=touched
    data['review']=review
    gate,reasons=evaluate(phase,data['checks'],review,errors=data['errors'],scope_violations=data['scope_violations'],evidence_complete=intact)
    data['gate']=gate;data['gate_reasons']=reasons
    data['execution_status']='WAITING_HUMAN_APPROVAL' if gate=='PASS' else 'COMPLETED'
    label=final_label(data,campaign)
    destination=ROOT/'docs/baselines'; names=('0d_2t_baseline_v1.json','0d_2t_baseline_v1.md')
    if label=='P0_PASS_BASELINE_FROZEN': preflight_destinations(destination,names)
    # Guardar evidencia del stub/unavailable: no reemplazar su procedencia por independencia ficticia.
    preserve(run_dir/'artifacts/pre-review-evidence.json',(run_dir/'evidence.json').read_bytes())
    preserve(run_dir/'artifacts/pre-review-summary.md',(run_dir/'summary.md').read_bytes())
    write_json(run_dir/'artifacts/independent-review.json',envelope)
    created=[]
    if label=='P0_PASS_BASELINE_FROZEN':
        baseline=baseline_document(campaign)
        destination.mkdir(parents=True,exist_ok=True)
        text=('\n'.join(['# Baseline 0D 2T v1','', '**NUMERICALLY_VERIFIED_BASELINE** — aceptación humana pendiente.',
            f"Commit fuente: `{campaign['git_commit']}`. Run: `{campaign['run_id']}`.",
            '',baseline['interpretation'],'',*baseline['limitations'],'',
            f"26/26 PASS; regresiones exactas. Stress: {campaign['stress_state']}.",
            'PerfilB, banda exterior100Pa, mínimo0,001°,60s/30ciclos/2MRHS/512MiB por punto.',
            'Parámetros completos, hashes, métricas de26puntos y stress en el manifest JSON adjunto.',
            'El rango público permanece2500–3500; no se inicia P1.','']))
        # Preparar ambos archivos completos primero, y crear destinos exclusivamente.
        write_json(run_dir/'artifacts'/names[0],baseline)
        (run_dir/'artifacts'/names[1]).write_text(text,encoding='utf-8')
        created=[]
        try:
            for name in names:
                with (destination/name).open('xb') as stream:
                    created.append(destination/name)
                    stream.write((run_dir/'artifacts'/name).read_bytes())
        except OSError:
            # Solo archivos nuevos creados por esta operación, nunca documentos previos.
            for path in created: path.unlink()
            raise
        data['files_changed'],data['scope_violations'],data['preexisting_touched']=compare(before,snapshot(ROOT),phase)
        if data['scope_violations']:
            data.update(gate='BLOCKED',gate_reasons=['scope_violation'],execution_status='COMPLETED');label='BLOCKED_SCOPE_VIOLATION'
    write_json(run_dir/'artifacts/p0-decision.json',dict(state=label,gate=data['gate'],execution_status=data['execution_status'],stress=campaign['stress_state'],next_phase_executed=False))
    additional=['artifacts/pre-review-evidence.json','artifacts/pre-review-summary.md','artifacts/independent-review.json','artifacts/p0-decision.json']
    if label=='P0_PASS_BASELINE_FROZEN': additional += ['artifacts/0d_2t_baseline_v1.json','artifacts/0d_2t_baseline_v1.md']
    data['artifacts']+=artifacts(run_dir,additional)
    data['finished_at']=datetime.now(timezone.utc).isoformat()
    try:
        build_report(run_dir,data)
        marker=run_dir/'artifacts/p0-finalized.tmp'
        write_json(marker,dict(evidence_sha256=sha(run_dir/'evidence.json'),state=label))
        marker.replace(run_dir/'artifacts/p0-finalized.json')
    except Exception:
        rollback_close(run_dir,created)
        raise
    print(json.dumps(dict(state=label,gate=data['gate'],execution_status=data['execution_status'],run_id=data['run_id']),indent=2))
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run_dir',type=Path);parser.add_argument('--review',type=Path,required=True)
    args=parser.parse_args();finalize(args.run_dir,args.review)
