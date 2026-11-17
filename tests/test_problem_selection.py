import importlib.util
import pathlib
from types import SimpleNamespace

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tdd_predict", ROOT / "upstream/LiveCodeBench/predict.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

def test_manifest_selection_is_order_independent(tmp_path):
    manifest = tmp_path / "ids.csv"
    manifest.write_text("question_id\nq1\nq3\n")
    tasks = [SimpleNamespace(question_id="q3"), SimpleNamespace(question_id="q2"), SimpleNamespace(question_id="q1")]
    selected = module.select_tasks(tasks, question_ids_file=manifest)
    assert [x.question_id for x in selected] == ["q1", "q3"]

def test_manifest_rejects_missing_id(tmp_path):
    manifest = tmp_path / "ids.csv"; manifest.write_text("question_id\nmissing\n")
    try: module.select_tasks([SimpleNamespace(question_id="q1")], question_ids_file=manifest)
    except ValueError as exc: assert "missing" in str(exc)
    else: raise AssertionError("missing ID was accepted")
