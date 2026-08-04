#!/usr/bin/env bash
set -euo pipefail

ROOT="mondrian_clique_2018"
DATA_DIR="${ROOT}/results/data_audit"
OUTPUT_DIR="${ROOT}/results/confirmation"
BASE_PARSER="real_shower_meta_stage0/audit_real_shower_data.py"
BASELINE_PAYLOAD="real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64"
EXPECTED_PARSER_BLOB="4a029051230f7c6e99b09e911f8a9e5228a58783"
EXPECTED_SOURCE_SHA256="f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"
EXPECTED_BASELINE_PAYLOAD_SHA256="2cb82a8c12913a6176ddd7c6333b57a4d672334934c0d2ca4b572e878590cfa2"
EXPECTED_BASELINE_SOURCE_SHA256="7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"

mkdir -p "${DATA_DIR}" "${OUTPUT_DIR}"

echo "== Verify and derive exact untouched-2018 parser =="
test "$(git hash-object "${BASE_PARSER}")" = "${EXPECTED_PARSER_BLOB}"
python - <<'PY'
from pathlib import Path

source = Path("real_shower_meta_stage0/audit_real_shower_data.py").read_text()
replacements = {
    'OUT_DIR = ROOT / "results" / "data_audit"': 'OUT_DIR = Path("mondrian_clique_2018/results/data_audit")',
    'YEARS = (2019, 2021, 2023, 2025)': 'YEARS = (2018,)',
    '''        profile["eligible"] = bool(
            profile["quality_events"] >= 200
            and profile["represented_years"] >= 3
            and profile["years_ge_20"] >= 3
        )''': '''        profile["eligible"] = bool(
            profile["quality_events"] >= 200
            and profile["represented_years"] == 1
            and profile["years_ge_20"] == 1
        )''',
    'profile["strong"] = bool(profile["quality_events"] >= 1000 and profile["represented_years"] == 4)': 'profile["strong"] = bool(profile["quality_events"] >= 300 and profile["represented_years"] == 1)',
    '"strong_showers_at_least_12": len(strong) >= 12': '"strong_showers_at_least_8": len(strong) >= 8',
    '"multi_shower_complex_units_at_least_6": len(multi_shower_complexes) >= 6': '"multi_shower_complex_units_at_least_2": len(multi_shower_complexes) >= 2',
    '"quality_sporadics_at_least_200000": total_sporadic_quality >= 200_000': '"quality_sporadics_at_least_50000": total_sporadic_quality >= 50_000',
    'GhostStream was excluded. Data came from 48 official GMN monthly trajectory summaries and the IAU MDC shower file.': 'Fresh confirmation data came from 12 official 2018 GMN monthly trajectory summaries and the IAU MDC shower file.',
}
for old, new in replacements.items():
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one source occurrence: {old!r}; got {count}")
    source = source.replace(old, new)
destination = Path("/tmp/audit_2018_data.py")
destination.write_text(source)
print("derived parser bytes:", destination.stat().st_size)
PY
python -m py_compile /tmp/audit_2018_data.py

echo "== Download and audit untouched 2018 data =="
python /tmp/audit_2018_data.py

echo "== Enforce frozen data and complete-year coverage gates =="
python - <<'PY'
import bisect
import gzip
import json
from pathlib import Path

root = Path("mondrian_clique_2018/results/data_audit")
audit = json.loads((root / "audit.json").read_text())
if tuple(audit["configuration"]["years"]) != (2018,):
    raise RuntimeError(f"Unexpected years: {audit['configuration']['years']}")
if not all(audit["gates"].values()):
    raise SystemExit(f"Frozen 2018 audit gates failed: {audit['gates']}")

sources = audit.get("sources", [])
source_gate = (
    len(sources) == 12
    and {int(item["month"]) for item in sources} == set(range(1, 13))
    and all(int(item.get("bytes", 0)) > 0 for item in sources)
)

events = []
with gzip.open(root / "selected_events.jsonl.gz", "rt", encoding="utf-8") as handle:
    for line in handle:
        event = json.loads(line)
        if int(event["year"]) != 2018:
            raise RuntimeError(f"Unexpected event year: {event['year']}")
        events.append(event)

sporadic_sols = sorted(
    float(event["sol"]) % 360.0
    for event in events
    if int(event["iau"]) == -1 and not (20.0 <= float(event["sol"]) <= 55.0)
)
extended = (
    [value - 360.0 for value in sporadic_sols]
    + sporadic_sols
    + [value + 360.0 for value in sporadic_sols]
)
supported = []
maximum_local_count = {}
for phase_bin in range(36):
    centers = [value for value in sporadic_sols if int(value // 10.0) == phase_bin]
    best = 0
    for center in centers:
        count = bisect.bisect_right(extended, center + 10.0) - bisect.bisect_left(extended, center - 10.0)
        best = max(best, count)
    maximum_local_count[str(phase_bin)] = best
    if best >= 128:
        supported.append(phase_bin)

coverage = {
    "year": 2018,
    "selected_events": len(events),
    "sporadics_after_blind": len(sporadic_sols),
    "supported_10deg_bins": supported,
    "supported_bin_count": len(supported),
    "maximum_local_count_by_bin": maximum_local_count,
    "gates": {
        "twelve_nonempty_monthly_sources": source_gate,
        "supported_10deg_bins_at_least_30": len(supported) >= 30,
    },
}
(root / "coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True))
print(json.dumps({
    "eligible_count": audit["eligible_count"],
    "strong_count": audit["strong_count"],
    "eligible_complex_units": audit["eligible_complex_units"],
    "total_quality_sporadics": audit["total_quality_sporadics"],
    "audit_gates": audit["gates"],
    "coverage": coverage,
}, indent=2))
if not all(coverage["gates"].values()):
    raise SystemExit(f"Frozen 2018 coverage gates failed: {coverage['gates']}")
PY

git hash-object "${BASE_PARSER}" > "${DATA_DIR}/base_source_blob_sha.txt"
sha256sum \
  "${ROOT}/PROTOCOL.md" \
  "${BASE_PARSER}" \
  "${DATA_DIR}/selected_events.jsonl.gz" \
  "${DATA_DIR}/audit.json" \
  "${DATA_DIR}/coverage.json" \
  > "${DATA_DIR}/source_and_data_sha256.txt"
python --version > "${DATA_DIR}/python_version.txt"

echo "== Verify exact passed PR38 candidate and baseline =="
echo "${EXPECTED_BASELINE_PAYLOAD_SHA256}  ${BASELINE_PAYLOAD}" | sha256sum -c -
python - <<'PY'
import base64
import gzip
import hashlib
import json
from pathlib import Path

expected_source = "f1c121e97a660a3820a11814c4325eb3ab33d34a031e83bdfb03b4b392e259b8"
expected_baseline = "7718ac5229475f4240305ad9c1e073c49702c771df36612d9be5baa877b46a50"

audit = json.loads(Path("mondrian_clique_2018/results/data_audit/audit.json").read_text())
coverage = json.loads(Path("mondrian_clique_2018/results/data_audit/coverage.json").read_text())
if tuple(audit["configuration"]["years"]) != (2018,):
    raise RuntimeError("Unexpected confirmation year")
if not all(audit["gates"].values()) or not all(coverage["gates"].values()):
    raise RuntimeError("Fresh 2018 data gate did not pass")

parts = sorted(Path("mondrian_clique_development/source_parts_v2").glob("part*.b64"))
expected_names = ["part00.b64", "part01.b64", "part02.b64", "part03.b64"]
if [part.name for part in parts] != expected_names:
    raise RuntimeError(f"Unexpected source parts: {[part.name for part in parts]}")
encoded = "".join("".join(part.read_text().split()) for part in parts)
if len(encoded) != 9000:
    raise RuntimeError(f"Unexpected encoded source length: {len(encoded)}")
source = gzip.decompress(base64.b64decode(encoded, validate=True))
source_hash = hashlib.sha256(source).hexdigest()
if source_hash != expected_source:
    raise RuntimeError(f"Confirmation source mismatch: {source_hash}")
Path("/tmp/run_mondrian_clique_2018.py").write_bytes(source)

baseline_encoded = "".join(Path("real_shower_meta_stage0/run_baseline_ceiling.py.gz.b64").read_text().split())
baseline_source = gzip.decompress(base64.b64decode(baseline_encoded, validate=True))
baseline_hash = hashlib.sha256(baseline_source).hexdigest()
if baseline_hash != expected_baseline:
    raise RuntimeError(f"Baseline source mismatch: {baseline_hash}")

print("selected events SHA-256:", hashlib.sha256(Path("mondrian_clique_2018/results/data_audit/selected_events.jsonl.gz").read_bytes()).hexdigest())
print("audit SHA-256:", hashlib.sha256(Path("mondrian_clique_2018/results/data_audit/audit.json").read_bytes()).hexdigest())
print("coverage SHA-256:", hashlib.sha256(Path("mondrian_clique_2018/results/data_audit/coverage.json").read_bytes()).hexdigest())
print("confirmation source SHA-256:", source_hash)
print("baseline source SHA-256:", baseline_hash)
PY
python -m py_compile /tmp/run_mondrian_clique_2018.py

echo "== Run one-shot untouched 2018 confirmation =="
python /tmp/run_mondrian_clique_2018.py \
  --events "${DATA_DIR}/selected_events.jsonl.gz" \
  --year 2018 \
  --corpus complete-year-2018-confirmation \
  --workers 4 \
  --baseline-payload "${BASELINE_PAYLOAD}" \
  --output "${OUTPUT_DIR}"
cat "${OUTPUT_DIR}/MONDRIAN_CLIQUE_DEVELOPMENT_2018.md"

echo "== Enforce frozen confirmation gates =="
python - <<'PY'
import json
from pathlib import Path

path = Path("mondrian_clique_2018/results/confirmation/mondrian_clique_development_2018.json")
result = json.loads(path.read_text())
if int(result["counts"]["minimum_supported_bins"]) != 20:
    raise SystemExit(f"Unexpected complete-year support rule: {result['counts']['minimum_supported_bins']}")
summary = {
    "counts": result["counts"],
    "candidate_weak_auc": result["candidate_weak_auc"],
    "comparators": result["fixed_comparator_weak_auc"],
    "false_positive": result["false_positive"],
    "worst_reporting_sector_0.05": result["worst_reporting_sector_0.05"],
    "recall": result["recall"],
    "fold_results": result["fold_results"],
    "gates": result["gates"],
    "source_verdict": result["verdict"],
}
print(json.dumps(summary, indent=2))
if not all(result["gates"].values()):
    raise SystemExit("Frozen fresh-2018 confirmation gate failed")

confirmation = {
    "verdict": "PASS_MONDRIAN_CLIQUE_2018_CONFIRMATION",
    "source_result": result,
}
Path("mondrian_clique_2018/results/confirmation/confirmation_verdict.json").write_text(
    json.dumps(confirmation, indent=2, sort_keys=True)
)
PY

sha256sum \
  "${ROOT}/PROTOCOL.md" \
  mondrian_clique_development/source_parts_v2/part00.b64 \
  mondrian_clique_development/source_parts_v2/part01.b64 \
  mondrian_clique_development/source_parts_v2/part02.b64 \
  mondrian_clique_development/source_parts_v2/part03.b64 \
  "${DATA_DIR}/selected_events.jsonl.gz" \
  "${DATA_DIR}/audit.json" \
  "${DATA_DIR}/coverage.json" \
  "${BASELINE_PAYLOAD}" \
  > "${OUTPUT_DIR}/source_and_input_sha256.txt"
python --version > "${OUTPUT_DIR}/python_version.txt"
python -m pip freeze > "${OUTPUT_DIR}/environment.txt"

echo "Frozen untouched-2018 confirmation passed every gate."
