import ast
import pathlib
import random
import subprocess
import sys

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'scripts/analyze_results.py'

def functions():
    tree = ast.parse(SCRIPT.read_text())
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    scope = {'random': random}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SCRIPT), 'exec'), scope)
    return scope

def test_resampling_and_adjustment():
    f = functions()
    assert f['bootstrap_ci']([0, 0], 100) == (0, 0)
    assert f['signflip_p']([0, 0], 100) == 1
    assert f['holm']([.01, .04, .03]) == [.03, .06, .06]
    assert f['bootstrap_ci']([-1, 0, 1], 100) == f['bootstrap_ci']([-1, 0, 1], 100)

def test_rejects_duplicate_and_missing(tmp_path):
    for body, message in [
        ('1,m,cot,1,evaluated,1\n'*2, 'Duplicate'),
        ('1,m,cot,1,evaluated,1\n', 'Incomplete')]:
        data = tmp_path/'attempts.csv'
        data.write_text('problem_id,model,condition,attempt,status,passed\n'+body)
        result = subprocess.run([sys.executable,str(SCRIPT),'--input',str(data)],capture_output=True,text=True)
        assert result.returncode != 0
        assert message in result.stderr
