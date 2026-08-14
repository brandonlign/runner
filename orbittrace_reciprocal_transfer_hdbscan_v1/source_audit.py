from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "orbittrace_reciprocal_transfer_hdbscan_v1" / "PROTOCOL.md"
KERNEL = ROOT / "orbittrace_reciprocal_transfer_hdbscan_v1" / "reciprocal_transfer.py"
RUNNER = ROOT / "orbittrace_reciprocal_transfer_hdbscan_v1" / "run_development.py"
EXPECTED = {
    "PROTOCOL.md": "6181ba8e4dfa34f869249389bda2eae46ca2c690",
    "reciprocal_transfer.py": "f3a7c8d5ea53bf856fb8d0225d5d578c4248e5ce",
    "run_development.py": "624b9d9855fa87e0e8331128af32eb88225d93cc",
}


def git_blob(path: Path) -> str:
    import subprocess
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def source_line_of(tree: ast.AST, predicate) -> list[int]:
    return sorted(int(node.lineno) for node in ast.walk(tree) if hasattr(node, "lineno") and predicate(node))


def call_name(node: ast.Call) -> str:
    f = node.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        parts = [f.attr]
        v = f.value
        while isinstance(v, ast.Attribute):
            parts.append(v.attr)
            v = v.value
        if isinstance(v, ast.Name):
            parts.append(v.id)
        return ".".join(reversed(parts))
    return ""


def main() -> None:
    for path in (PROTOCOL, KERNEL, RUNNER):
        require(git_blob(path) == EXPECTED[path.name], f"frozen source drift: {path.name}")

    kernel_text = KERNEL.read_text()
    runner_text = RUNNER.read_text()
    ktree = ast.parse(kernel_text)
    rtree = ast.parse(runner_text)

    # Kernel has no access path to truth, external comparators, or parent outputs.
    lowered = kernel_text.lower()
    for forbidden in (
        "hidden_sealed",
        "parent_result",
        "parent_prelabel",
        "sonotaco",
        "maarsy",
        "dms",
        "orbittrace target",
        "shower_code",
    ):
        require(forbidden not in lowered, f"kernel contains forbidden scientific surface: {forbidden}")

    require("best_count * 2 > idx.size" in kernel_text, "strict-majority rule changed")
    require("prediction_data=True" in kernel_text, "prediction-data requirement changed")
    require("min_cluster_size=MIN_CLUSTER_SIZE" in kernel_text, "min_cluster_size call changed")
    require("min_samples=MIN_SAMPLES" in kernel_text, "min_samples call changed")
    require("cluster_selection_method=\"eom\"" in kernel_text, "EOM selection changed")
    require("cluster_selection_epsilon=0.0" in kernel_text, "epsilon changed")
    require("allow_single_cluster=False" in kernel_text, "single-cluster setting changed")
    require("approximate_predict(model23, X22)" in kernel_text, "2022->2023 transport changed")
    require("approximate_predict(model22, X23)" in kernel_text, "2023->2022 transport changed")

    # Probability arrays are outputs only. They must never be arguments to strict
    # majority mapping or appear in the candidate ranking sort key.
    majority_calls = [
        node for node in ast.walk(ktree)
        if isinstance(node, ast.Call) and call_name(node).endswith("strict_majority_mapping")
    ]
    require(len(majority_calls) == 2, "expected exactly two strict-majority mapping calls")
    for node in majority_calls:
        arg_src = " ".join(ast.unparse(a) for a in node.args)
        require("prob" not in arg_src.lower(), "prediction probability entered majority matching")

    sort_calls = [
        node for node in ast.walk(ktree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "sort"
    ]
    require(sort_calls, "candidate ranking sort missing")
    ranking_src = "\n".join(ast.unparse(node) for node in sort_calls)
    require("majority_fraction" not in ranking_src, "majority fraction entered ranking")
    require("prob" not in ranking_src.lower(), "prediction probability entered ranking")
    for required in ("worst_year_persistence", "best_year_persistence", "n_2022", "n_2023", "family_id"):
        require(required in ranking_src, f"ranking key missing {required}")

    # Runner ordering: complete successor prelabel write must occur before parent
    # JSON reads or the explicit hidden truth unseal assignment.
    prelabel_write = source_line_of(
        rtree,
        lambda n: isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "write_text"
        and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "prelabel_path",
    )
    require(len(prelabel_write) == 1, "prelabel write boundary ambiguous")
    freeze_line = prelabel_write[0]

    parent_reads = source_line_of(
        rtree,
        lambda n: isinstance(n, ast.Call)
        and call_name(n) == "json.loads"
        and any("parent_" in ast.unparse(a) for a in n.args),
    )
    require(parent_reads and min(parent_reads) > freeze_line, "parent output read occurs before successor prelabel freeze")

    hidden_unseal = source_line_of(
        rtree,
        lambda n: isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "hidden" for t in n.targets)
        and isinstance(n.value, ast.Name)
        and n.value.id == "hidden_sealed",
    )
    require(len(hidden_unseal) == 1 and hidden_unseal[0] > freeze_line, "truth unseal occurs before successor prelabel freeze")

    build_calls = source_line_of(
        rtree,
        lambda n: isinstance(n, ast.Call) and call_name(n).endswith("build_reciprocal_transfer"),
    )
    require(len(build_calls) == 1 and build_calls[0] < freeze_line, "successor construction not completed before prelabel freeze")

    # No parent/truth value is passed into the successor kernel.
    for node in ast.walk(rtree):
        if isinstance(node, ast.Call) and call_name(node).endswith("build_reciprocal_transfer"):
            args = [ast.unparse(a) for a in node.args]
            require(args == ["X22", "ids22", "X23", "ids23"], f"successor kernel inputs changed: {args}")

    payload = {
        "verdict": "PASS_RECIPROCAL_TRANSFER_HDBSCAN_V1_SOURCE_AUDIT",
        "frozen_blobs": EXPECTED,
        "prelabel_freeze_line": freeze_line,
        "first_parent_output_read_line": min(parent_reads),
        "truth_unseal_line": hidden_unseal[0],
        "successor_build_line": build_calls[0],
        "prediction_probabilities_enter_matching": False,
        "prediction_probabilities_enter_ranking": False,
        "majority_fractions_enter_ranking": False,
        "kernel_truth_surface": False,
        "scientific_data_accessed": False,
        "gmn_accessed": False,
        "truth_accessed": False,
        "sonotaco_accessed": False,
        "amos_accessed": False,
        "efn_accessed": False,
        "orbittrace_target_access": False,
        "maarsy_scientific_access": False,
        "dms_scientific_access": False,
    }
    out = ROOT / "output_reciprocal_transfer_source_audit"
    out.mkdir(parents=True, exist_ok=True)
    result = out / "RECIPROCAL_TRANSFER_HDBSCAN_V1_SOURCE_AUDIT.json"
    result.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    payload["result_sha256"] = hashlib.sha256(result.read_bytes()).hexdigest()
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
