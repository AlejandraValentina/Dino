"""Small synthetic one-cycle integration check for the Desktop factorial adapter."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from motorsim.desktop.services import new_design_project
from motorsim.design_study import available_parameters, prepare_factorial_design_study, run_design_study

parser=argparse.ArgumentParser()
parser.add_argument('--artifact-root',required=True)
parser.add_argument('--study-id',required=True)
args=parser.parse_args()
project=new_design_project('synthetic-factorial-integration')
engine=project['base_engine']
parameters=available_parameters(engine)
port=next(item for item in parameters if item['id']=='port:primary-window:top_mm')
crankcase=next(item for item in parameters if item['id']=='crankcase.volume_bdc_cm3')
prepared=prepare_factorial_design_study(engine,factors=[
 {'parameter_id':port['id'],'values':[port['baseline'],port['baseline']+1.0]},
 {'parameter_id':crankcase['id'],'values':[crankcase['baseline'],crankcase['baseline']+5.0]},
],rpm=3000,max_cycles=1,point_budget_seconds=45,total_budget_seconds=180,
 memory_limit_mib=512,project_id=project['project_id'],
 variant_label='SINTETICO · factorial Desktop',study_id=args.study_id)
result=run_design_study(prepared,artifact_root=Path(args.artifact_root))
summary={'status':result['status'],'study_id':result['study_id'],
 'manifest':result['design_study_manifest'],'elapsed_seconds':result['elapsed_seconds'],
 'scientific_validation':result['scientific_validation'],
 'points':[{'status':p['status'],'label':p.get('label'),'identity_sha256':p.get('identity_sha256'),
  'classification':p.get('classification'),'periodicity':p.get('periodicity'),
  'cycles_completed':p.get('cycles_completed'),'result_artifact_sha256':p.get('result_artifact_sha256'),
  'factor_values':p.get('factor_values')} for p in result['points']]}
print(json.dumps(summary,ensure_ascii=False,indent=2))
