from __future__ import annotations

import json
import math
from pathlib import Path

import rebound

OUT_DIR = Path("covariance_flow_stage0/results/rebound_probe")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    simulation = rebound.Simulation()
    # REBOUND 5.x loads the packaged test configuration through Simulation.add.
    simulation.add("outer solar system")
    simulation.integrator = "ias15"
    simulation.move_to_com()

    particle_count = len(simulation.particles)
    initial_energy = simulation.energy()
    simulation.integrate(-2.0 * math.pi)
    final_energy = simulation.energy()
    relative_error = abs((final_energy - initial_energy) / initial_energy)

    sun = simulation.particles[0]
    simulation.add(
        primary=sun,
        m=0.0,
        a=2.5,
        e=0.2,
        inc=math.radians(10.0),
        Omega=math.radians(80.0),
        omega=math.radians(40.0),
        M=math.radians(15.0),
    )
    test_particle = simulation.particles[-1]
    orbit = test_particle.orbit(primary=sun)

    payload = {
        "rebound_version": rebound.__version__,
        "packaged_initial_conditions": "outer solar system",
        "particle_count_outer_solar_system": particle_count,
        "initial_energy": initial_energy,
        "final_energy_after_one_nominal_year_backward": final_energy,
        "relative_energy_error": relative_error,
        "test_particle_orbit": {
            "a": orbit.a,
            "e": orbit.e,
            "inc": orbit.inc,
            "Omega": orbit.Omega,
            "omega": orbit.omega,
            "M": orbit.M,
        },
        "passed": bool(
            particle_count >= 5
            and relative_error <= 1e-10
            and abs(orbit.a - 2.5) <= 1e-6
            and abs(orbit.e - 0.2) <= 1e-6
        ),
    }
    (OUT_DIR / "probe.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = "\n".join(
        [
            "# REBOUND packaged-Solar-System probe",
            "",
            f"- version: `{payload['rebound_version']}`",
            f"- packaged particles: `{particle_count}`",
            f"- one-year backward relative energy error: `{relative_error:.6e}`",
            f"- test-particle orbit recovered: `{payload['test_particle_orbit']}`",
            f"- verdict: **{'PASS' if payload['passed'] else 'FAIL'}**",
        ]
    )
    (OUT_DIR / "PROBE_REPORT.md").write_text(report, encoding="utf-8")
    print(report)
    if not payload["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
