from pathlib import Path
import hashlib

SRC = Path('orbittrace_m2d_sacv_dual_output_core_v1/run_binding.generated.sh')
DST = Path('orbittrace_m2d_sacv_topomodal_trunk_core_v1/run_binding.generated.sh')
s = SRC.read_text()

replacements = [
    ('orbittrace_m2d_sacv_dual_output_core_v1', 'orbittrace_m2d_sacv_topomodal_trunk_core_v1'),
    ('m2d-sacv-dual-output-core-v1', 'm2d-sacv-topomodal-trunk-core-v1'),
    ('M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_PRETRUTH', 'M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_GMN_PRETRUTH'),
    ('M2D_SACV_DUAL_OUTPUT_CORE_V1_GMN_RESULT', 'M2D_SACV_TOPOMODAL_TRUNK_CORE_V1_GMN_RESULT'),
    ('SACV_DUAL_OUTPUT_CORE_GMN_PRETRUTH_SEALED', 'SACV_TOPOMODAL_TRUNK_CORE_GMN_PRETRUTH_SEALED'),
]
for old, new in replacements:
    if old not in s:
        raise RuntimeError(f'missing runner token {old}')
    s = s.replace(old, new)

# Replace only the exact #1418 prospective source pins with the #1419 frozen sources.
for old, new in {
    'f0fa84f5062c4719433727719b8451404db9ef9c3f5b4892f591dbeb898173c2': '474a9b082376365834c1d59020f0e6b35e4e2dcdb455a82e535a093a3b562cd1',
    '93944133a1dad77d19238ace58ec0c7301a6ad5461268188ccfadefb6e074e22': 'eaa146b1b04f2a30bbe86ffc4393a9b2e10580f7ed09ef7a22dd1dc8f280069c',
    '3e71fe4ea4b75922ea24cefe61fdc14c76003bbe9a83dc9a4519c9333d3f9b6d': '050c6a7aa4acdb868f73667a427fdc5f9e2e3f3a7c9e15e0f1b5ee03c2368a87',
}.items():
    if s.count(old) != 1:
        raise RuntimeError(f'expected one inherited source pin {old}, saw {s.count(old)}')
    s = s.replace(old, new, 1)

# The hidden-truth path is allowed only after the exact audited instrumentation
# has been applied to the otherwise-frozen fallback recurrence runtime.
anchor = 'ROOT="$PWD"\n'
insert = anchor + "test \"$(sha256sum orbittrace_m2d_sacv_topomodal_trunk_core_v1/instrument_runtime.py | cut -d' ' -f1)\" = 'e00cab798ba3a0224afedf81dedd191bb55bc35398c3d10f1b36237421636213'\n" + "test \"$(sha256sum orbittrace_m2d_sacv_fallback_recurrence_v1/build_pretruth.py | cut -d' ' -f1)\" = '7beb50b31dd0e4b440bf5b62e5da14a9e92e82497b2576d8006dcb934453ceaa'\n" + "echo PASS_AUDITED_INSTRUMENTED_FALLBACK_RUNTIME\n"
if s.count(anchor) != 1:
    raise RuntimeError(f'ROOT anchor count {s.count(anchor)}')
s = s.replace(anchor, insert, 1)

# Tighten the pretruth integrity printout to the prospective role while retaining
# all inherited primary/firewall assertions.
needle = "assert r['shower_truth_used'] is False and r['target_information_access'] is False and r['target_region_events_accessed'] is False\n"
extra = needle + "assert r['scientific_role']=='TARGET_EXCLUDED_SACV_PRIMARY_PLUS_TOPOMODAL_TRUNK_RECURRENT_CORE_FROZEN_BEFORE_SHOWER_TRUTH'\nassert r['primary_output_exact_sacv_v1'] is True and r['nested_core_changes_primary_matching'] is False\n"
if s.count(needle) != 1:
    raise RuntimeError(f'pretruth firewall anchor count {s.count(needle)}')
s = s.replace(needle, extra, 1)

DST.write_text(s)
print('run_binding.generated.sh', hashlib.sha256(DST.read_bytes()).hexdigest(), DST.stat().st_size)
