"""Generate API config safely; never put API credentials into a tracked file."""
import argparse, os, pathlib, shutil, yaml
P=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--base-url',default='https://api.openai.com/v1');p.add_argument('--max-tokens',type=int,default=4096);p.add_argument('--temperature',type=float);a=p.parse_args()
if not os.getenv('OPENAI_API_KEY'):raise SystemExit('Missing OPENAI_API_KEY in environment. Do not paste it into files or chat.')
up=P/'upstream';
for rel in ['LiveCodeBench/config/config.yaml','LiveCodeBench/predict.py','LiveCodeBench/config/model.yaml']:
 if not (up/rel).exists():raise SystemExit(f'Missing upstream/{rel}; run bash scripts/setup.sh first')
out=P/'config'/'local_model.yaml'
kwargs={'max_tokens':a.max_tokens}
if a.temperature is not None:kwargs['temperature']=a.temperature
out.write_text(yaml.safe_dump({'model':{'model_name':a.model,'base_url':a.base_url,'api_key':os.environ['OPENAI_API_KEY'],'model_kwargs':kwargs}}))
out.chmod(0o600)
print('Created local untracked model config:',out)
print('WARNING: this file contains your API key. Never upload or commit it.')
