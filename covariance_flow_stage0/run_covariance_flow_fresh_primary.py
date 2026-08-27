from __future__ import annotations

import math

import numpy as np
import rebound

import run_covariance_flow as base
import run_covariance_flow_recording as recording


def local_flow_fresh_primary(events: list[dict[str, object]]) -> base.FlowResult:
    medoid = base.group_medoid(events)
    center = base.event_feature(medoid)
    mean_anomaly = base.event_mean_anomaly_deg(medoid)
    simulation = rebound.Simulation()
    simulation.add("outer solar system")
    simulation.integrator = "ias15"
    simulation.move_to_com()
    initial_energy = simulation.energy()

    for column in range(5):
        plus = center.copy()
        minus = center.copy()
        plus[column] += base.FLOW_STEP
        minus[column] -= base.FLOW_STEP
        base.add_particle_from_feature(
            simulation,
            simulation.particles[0],
            plus,
            mean_anomaly,
        )
        base.add_particle_from_feature(
            simulation,
            simulation.particles[0],
            minus,
            mean_anomaly,
        )

    simulation.integrate(-base.LOOKBACK_YEARS * 2.0 * math.pi)
    final_energy = simulation.energy()
    relative_error = abs((final_energy - initial_energy) / initial_energy)
    if relative_error > base.ENERGY_TOLERANCE:
        raise RuntimeError(f"Energy error {relative_error} exceeds gate")

    final_sun = simulation.particles[0]
    jacobian = np.zeros((5, 5), dtype=np.float64)
    first_test_particle = 5
    for column in range(5):
        plus_feature = base.orbit_to_feature(
            simulation.particles[first_test_particle + 2 * column],
            final_sun,
        )
        minus_feature = base.orbit_to_feature(
            simulation.particles[first_test_particle + 2 * column + 1],
            final_sun,
        )
        jacobian[:, column] = (
            plus_feature - minus_feature
        ) / (2.0 * base.FLOW_STEP)
    if not np.all(np.isfinite(jacobian)):
        raise RuntimeError("Non-finite local flow Jacobian")
    return base.FlowResult(
        jacobian=jacobian,
        relative_energy_error=relative_error,
        medoid_event_id=str(medoid["id"]),
    )


base.local_flow = local_flow_fresh_primary


if __name__ == "__main__":
    recording.main()
