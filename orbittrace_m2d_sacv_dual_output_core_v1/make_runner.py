from pathlib import Path
import hashlib

SRC = Path('orbittrace_m2d_sacv_fallback_recurrence_v1/run_binding.sh')
DST = Path('orbittrace_m2d_sacv_dual_output_core_v1/run_binding.generated.sh')
s = SRC.read_text()

# Transport/name changes only.
s = s.replace('orbittrace_m2d_sacv_fallback_recurrence_v1', 'orbittrace_m2d_sacv_dual_output_core_v1')
s = s.replace('m2d-sacv-fallback-recurrence-v1', 'm2d-sacv-dual-output-core-v1')
s = s.replace('M2D_SACV_FALLBACK_RECURRENCE_V1_GMN_PRETRUTH', 'M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_PRETRUTH')
s = s.replace('M2D_SACV_FALLBACK_RECURRENCE_V1_GMN_RESULT', 'M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_RESULT')
s = s.replace('SACV_FALLBACK_RECURRENCE_GMN_PRETRUTH_SEALED', 'SACV_DUAL_OUTPUT_CORE_GMN_PRETRUTH_SEALED')

# Pin exact prospective protocol/scientific source identities.
repl = {
    'd1a29d1403194557019ba69fc1e1acb6314cd97cd81e88a8a66c9872fb72cab1': 'f0fa84f5062c4719433727719b8451404db9ef9c3f5b4892f591dbeb898173c2',
    'd4634839cc35dffa0cf8965923b21b048125844900c7a911515a389063067948': '93944133a1dad77d19238ace58ec0c7301a6ad5461268188ccfadefb6e074e22',
    'b082a003030309ec55ea16add7195829b876b680e1c449224c89d33c192465e6': '3e71fe4ea4b75922ea24cefe61fdc14c76003bbe9a83dc9a4519c9333d3f9b6d',
}
for old, new in repl.items():
    if s.count(old) != 1:
        raise RuntimeError(f'expected exactly one runner provenance literal {old}, saw {s.count(old)}')
    s = s.replace(old, new, 1)

# The already-downloaded #1405 artifact supplies the immutable per-candidate
# SACV-v1 primary membership oracle. Pin it before any prospective pretruth build.
needle = "test \"$(sha256sum \"$IN/sacvbase/truth/M2D_SACV_V1_GMN_RESULT.json\" | cut -d' ' -f1)\" = 'b9dedd36f0d409bbd31654c986354bcae43a64aa123c47bc19c3ccd221f86a36'\n"
insert = needle + "test \"$(sha256sum \"$IN/sacvbase/pretruth/M2D_SACV_V1_GMN_PRETRUTH.json\" | cut -d' ' -f1)\" = '77528fbec227bf8d8d311b9054c46db43668d7f12e9460b85db680c4a6ce927b'\n"
if s.count(needle) != 1:
    raise RuntimeError('SACV baseline result anchor not unique')
s = s.replace(needle, insert, 1)

# Add the oracle only to the prospective builder/evaluator. No metric or gate changes.
build_needle = '  --geometry "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json" \\\n  --output "$OUT/pretruth/M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_PRETRUTH.json"\n'
build_insert = '  --geometry "$OUT/pretruth/GMN_LABEL_FREE_GEOMETRY.json" \\\n  --sacv-v1-pretruth "$IN/sacvbase/pretruth/M2D_SACV_V1_GMN_PRETRUTH.json" \\\n  --output "$OUT/pretruth/M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_PRETRUTH.json"\n'
if s.count(build_needle) != 1:
    raise RuntimeError(f'builder invocation anchor count {s.count(build_needle)}')
s = s.replace(build_needle, build_insert, 1)

eval_needle = '  --sacv-pretruth "$OUT/pretruth/M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_PRETRUTH.json" \\\n  --internal-prelabel "$IN/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json" \\\n'
eval_insert = '  --sacv-pretruth "$OUT/pretruth/M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_PRETRUTH.json" \\\n  --sacv-v1-pretruth "$IN/sacvbase/pretruth/M2D_SACV_V1_GMN_PRETRUTH.json" \\\n  --internal-prelabel "$IN/internal/SUPPORT_CUT_BIFILTRATION_INTERNAL_MASS_V1_PRELABEL.json" \\\n'
if s.count(eval_needle) != 1:
    raise RuntimeError(f'evaluator invocation anchor count {s.count(eval_needle)}')
s = s.replace(eval_needle, eval_insert, 1)

DST.write_text(s)
print('run_binding.generated.sh', hashlib.sha256(DST.read_bytes()).hexdigest(), DST.stat().st_size)
