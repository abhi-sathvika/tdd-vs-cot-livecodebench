import sys,json,pathlib
for name in sys.argv[1:]:
 p=pathlib.Path(name); rows=json.loads(p.read_text());
 if not isinstance(rows,list):raise SystemExit(f'{p}: expected list')
 n=sum(len(r.get('code_list',[])) for r in rows)
 blank=sum(1 for r in rows for c in r.get('code_list',[]) if not c or c in ['Error',''])
 print(f'{p.name}: tasks={len(rows)} samples={n} empty_or_error={blank}')
print('NOTE: This is output validation, NOT correctness evaluation. Use official LiveCodeBench evaluator for pass@1.')
