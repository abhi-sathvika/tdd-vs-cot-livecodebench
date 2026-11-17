"""Launch official upstream LiveCodeBench experiment in separate processes."""
import argparse,datetime,hashlib,json,os,pathlib,platform,subprocess,sys,yaml
from dotenv import load_dotenv
P=pathlib.Path(__file__).resolve().parents[1];U=P/'upstream'
load_dotenv(P/'.env',override=True)
p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=5);p.add_argument('--samples',type=int,default=1);p.add_argument('--modes',nargs='+',choices=['cot','tdd','one_shot','self_plan','scot','icot','tdd_ablation'],default=['cot','tdd']);p.add_argument('--question-ids-file');p.add_argument('--output-dir');p.add_argument('--resume',action='store_true');p.add_argument('--execute',action='store_true');a=p.parse_args()
assert 0<=a.start<a.end and a.samples>=1
conf=P/'config'/'local_model.yaml'
if not (U/'LiveCodeBench/predict.py').exists():raise SystemExit('Run setup.sh first')
if not conf.exists():raise SystemExit('Run scripts/prepare.py first')
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=U,text=True).strip()
repo_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=P,text=True).strip()
evaluator_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=P/'official_livecodebench',text=True).strip()
model_cfg=yaml.safe_load(conf.read_text())['model']
prompt_path=U/'LiveCodeBench/config/config.yaml'
prompt_hash=hashlib.sha256(prompt_path.read_bytes()).hexdigest()
id_hash=(hashlib.sha256(pathlib.Path(a.question_ids_file).read_bytes()).hexdigest() if a.question_ids_file else None)
tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
root=pathlib.Path(a.output_dir).resolve() if a.output_dir else P/'runs'/f'{tag}_{a.start}_{a.end}'
root.mkdir(parents=True,exist_ok=a.resume)
commands=[]
for mode in a.modes:
 output=root/f'{mode}.json'
 command=[sys.executable,'LiveCodeBench/predict.py','--config_path','LiveCodeBench/config/config.yaml','--model_config',str(conf.resolve()),'--mode',mode,'--max_workers','1','--inner_workers','1','--max_retries','2','--timeout','180','--num_samples',str(a.samples),'--start',str(a.start),'--end',str(a.end),'--output_path',str(output)]
 if a.question_ids_file:command.extend(['--question_ids_file',str(pathlib.Path(a.question_ids_file).resolve())])
 commands.append({'mode':mode,'command':command,'output':str(output)})
(root/'manifest.json').write_text(json.dumps({'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository_commit':repo_commit,'upstream_commit':commit,'livecodebench_commit':evaluator_commit,'dataset':'livecodebench/code_generation_lite','dataset_release':'release_v6','provider':model_cfg.get('provider'),'model':model_cfg.get('model_name'),'base_url':model_cfg.get('base_url'),'model_kwargs':model_cfg.get('model_kwargs',{}),'python':platform.python_version(),'prompt_sha256':prompt_hash,'problem_manifest_sha256':id_hash,'start':a.start,'end':a.end,'samples':a.samples,'modes':a.modes,'question_ids_file':a.question_ids_file,'commands':commands,'note':'Commands use pinned TDD-Agent predict.py; separate processes / no conversation IDs. No credentials are recorded.'},indent=2))
print('Run manifest:',root/'manifest.json')
for item in commands:
 print('Mode:',item['mode'],'Output:',item['output'])
 if not a.execute:continue
 if a.resume and pathlib.Path(item['output']).exists():
  try:
   rows=json.loads(pathlib.Path(item['output']).read_text())
   expected=(sum(1 for line in pathlib.Path(a.question_ids_file).read_text().splitlines() if line.strip() and not line.startswith('question_id')) if a.question_ids_file else a.end-a.start)
   if len(rows)==expected and all(len(row.get('code_list',[]))==a.samples for row in rows):
    print('Resume: preserving complete output',item['output']);continue
  except (OSError,ValueError,TypeError):pass
  raise SystemExit(f"Refusing to overwrite incomplete output during resume: {item['output']}")
 with (root/f'{item["mode"]}.log').open('w') as log:
  rc=subprocess.call(item['command'],cwd=U,stdout=log,stderr=subprocess.STDOUT)
 print('Exit:',rc,'Log:',root/f'{item["mode"]}.log')
 if rc:raise SystemExit(f'Failed mode {item["mode"]}; inspect log. Existing outputs retained.')
if not a.execute:print('Dry-run only. Rerun with --execute to call paid APIs.')
