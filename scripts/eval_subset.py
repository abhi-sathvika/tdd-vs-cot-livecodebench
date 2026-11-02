import json
import sys

from lcb_runner.runner.parser import get_args
from lcb_runner.utils.scenarios import Scenario
from lcb_runner.evaluation import extract_instance_results
from lcb_runner.runner.scenario_router import (
    build_prompt_benchmark,
    sort_and_extract_save_results,
    get_metrics,
)

def qid_of(instance):
    if hasattr(instance, "question_id"):
        return str(instance.question_id)
    if hasattr(instance, "get_question_id"):
        return str(instance.get_question_id())
    raise RuntimeError(
        f"Could not find question_id on benchmark object of type {type(instance)}"
    )

def main():
    args = get_args()

    benchmark, _ = build_prompt_benchmark(args)

    with open(args.custom_output_file, "r") as f:
        rows = json.load(f)

    if not isinstance(rows, list) or not rows:
        raise SystemExit("Input file must contain a non-empty JSON list.")

    wanted_ids = {str(row["question_id"]) for row in rows}

    print("Requested question IDs:", sorted(wanted_ids))
    print("Full benchmark size:", len(benchmark))

    benchmark = [
        instance
        for instance in benchmark
        if qid_of(instance) in wanted_ids
    ]

    print("Matched benchmark tasks:", len(benchmark))

    if len(benchmark) != len(rows):
        found = {qid_of(x) for x in benchmark}
        missing = wanted_ids - found
        raise SystemExit(
            f"Could not match all generated outputs. Missing IDs: {sorted(missing)}"
        )

    if args.scenario not in [Scenario.codegeneration, Scenario.selfrepair]:
        raise SystemExit(
            f"This subset helper currently supports code generation only, got {args.scenario}"
        )

    rows = sorted(rows, key=lambda x: str(x["question_id"]))
    benchmark = sorted(benchmark, key=qid_of)

    custom_outputs = [row["code_list"] for row in rows]

    save_results = [
        instance.insert_output(output, output)
        for instance, output in zip(benchmark, custom_outputs)
    ]

    save_results, combined_results = sort_and_extract_save_results(
        args.scenario,
        save_results,
    )

    metrics = get_metrics(
        args.scenario,
        args,
        benchmark,
        combined_results,
    )

    graded = extract_instance_results(metrics[1])

    print("\n=== METRICS ===")
    print(json.dumps(metrics[0], indent=2))

    if args.scenario == Scenario.codegeneration:
        metadatas = metrics[2]

        save_eval_results = [
            instance.insert_output_evaluation(
                outputs_list,
                extracted_list,
                graded_list,
                metadata=meta,
            )
            for instance, (outputs_list, extracted_list), graded_list, meta
            in zip(benchmark, combined_results, graded, metadatas)
        ]
    else:
        save_eval_results = []

    output_path = args.custom_output_file[:-5] + "_subset_eval.json"

    with open(output_path, "w") as f:
        json.dump(save_eval_results, f, indent=2)

    print("\nDetailed evaluation saved to:")
    print(output_path)

if __name__ == "__main__":
    main()
