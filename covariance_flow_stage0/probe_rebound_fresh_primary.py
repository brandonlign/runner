from __future__ import annotations

import json
import math
from pathlib import Path

import rebound

OUT_DIR = Path("covariance_flow_stage0/results/fresh_primary_probe")
PERTURBATIONS = (
    (1.0e-5, 0.0, 0.0, 0.0, 0.0),
    (-1.0e-5, 0.0, 0.0, 0.0, 0.0),
    (0.0, 1.0e-5, 0.0, 0.0, 0.0),
    (0.0, -1.0e-5, 0.0, 0.0, 0.0),
    (0.0, 0.0, 1.0e-4, 0.0, 0.0),
    (0.0, 0.0, -1.0e-4, 0.0, 0.0),
    (0.0, 0.0, 0.0, 1.0e-4, 0.0),
    (0.0, 0.0, 0.0, -1.0e-4, 0.0),
    (0.0, 0.0, 0.0, 0.0, 1.0e-4),
    (0.0, 0.0, 0.0, 0.0, -1.0e-4),
)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    simulation = rebound.Simulation()
    simulation.add("outer solar system")
    simulation.integrator = "ias15"
    simulation.move_to_com()
    initial_energy = simulation.energy()

    for da, de, di, d_omega, d_node in PERTURBATIONS:
        simulation.add(
            primary=simulation.particles[0],
            m=0.0,
            a=2.5 + da,
            e=0.2 + de,
            inc=math.radians(10.0 + di),
            Omega=math.radians(80.0 + d_node),
            omega=math.radians(40.0 + d_omega),
            M=math.radians(15.0),
        )

    simulation.integrate(-100.0 * 2.0 * math.pi)
    final_energy = simulation.energy()
    relative_error = abs((final_energy - initial_energy) / initial_energy)
    final_sun = simulation.particles[0]
    orbits = []
    for index in range(5, 15):
        orbit = simulation.particles[index].orbit(primary=final_sun)
        orbits.append(
            {
                "index": index,
                "a": orbit.a,
                "e": orbit.e,
                "inc_deg": math.degrees(orbit.inc),
                "bound": bool(
                    math.isfinite(orbit.a)
                    and math.isfinite(orbit.e)
                    and orbit.a > 0.0
                    and 0.0 <= orbit.e < 1.0
                ),
            }
        )

    passed = relative_error <= 1.0e-8 and all(item["bound"] for item in orbits)
    payload = {
        "rebound_version": rebound.__version__,
        "lookback_years": 100.0,
        "relative_energy_error": relative_error,
        "orbits": orbits,
        "passed": passed,
    }
    (OUT_DIR / "probe.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = "\n".join(
        [
            "# REBOUND fresh-primary multi-particle probe",
            "",
            f"- relative energy error: `{relative_error:.6e}`",
            f"- bound final test particles: `{sum(item['bound'] for item in orbits)}/10`",
            f"- verdict: **{'PASS' if passed else 'FAIL'}**",
        ]
    )
    (OUT_DIR / "PROBE_REPORT.md").write_text(report, encoding="utf-8")
    print(report)
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
