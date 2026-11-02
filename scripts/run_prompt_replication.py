"""Launch official upstream LiveCodeBench experiment in separate processes."""
import argparse,datetime,hashlib,json,os,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parents[1];U=P/'upstream'
p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=5);p.add_argument('--samples',type=int,default=1);p.add_argument('--modes',nargs='+',choices=['cot','tdd','one_shot','self_plan','scot','icot','tdd_ablation'],default=['cot','tdd']);p.add_argument('--execute',action='store_true');a=p.parse_args()
assert 0<=a.start<a.end and a.samples>=1
conf=P/'config'/'local_model.yaml'
if not (U/'LiveCodeBench/predict.py').exists():raise SystemExit('Run setup.sh first')
if not conf.exists():raise SystemExit('Run scripts/prepare.py first')
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=U,text=True).strip()
tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
root=P/'runs'/f'{tag}_{a.start}_{a.end}';root.mkdir(parents=True,exist_ok=False)
commands=[]
for mode in a.modes:
 output=root/f'{mode}.json'
 command=[sys.executable,'LiveCodeBench/predict.py','--config_path','LiveCodeBench/config/config.yaml','--model_config',str(conf.resolve()),'--mode',mode,'--max_workers','1','--inner_workers','1','--max_retries','2','--timeout','180','--num_samples',str(a.samples),'--start',str(a.start),'--end',str(a.end),'--output_path',str(output)]
 commands.append({'mode':mode,'command':command,'output':str(output)})
(root/'manifest.json').write_text(json.dumps({'upstream_commit':commit,'start':a.start,'end':a.end,'samples':a.samples,'modes':a.modes,'commands':commands,'note':'Commands use official TDD-Agent upstream predict.py; separate processes / no conversation IDs.'},indent=2))
print('Run manifest:',root/'manifest.json')
for item in commands:
 print('Mode:',item['mode'],'Output:',item['output'])
 if not a.execute:continue
 with (root/f'{item["mode"]}.log').open('w') as log:
  rc=subprocess.call(item['command'],cwd=U,stdout=log,stderr=subprocess.STDOUT)
 print('Exit:',rc,'Log:',root/f'{item["mode"]}.log')
 if rc:raise SystemExit(f'Failed mode {item["mode"]}; inspect log. Existing outputs retained.')
if not a.execute:print('Dry-run only. Rerun with --execute to call paid APIs.')
