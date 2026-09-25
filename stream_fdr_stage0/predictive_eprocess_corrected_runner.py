from __future__ import annotations

import math

import numpy as np

import predictive_eprocess_pilot as pilot

EXTERNAL_PER_YEAR_EVENTS = 60


def corrected_evaluate_m2026(
    catalogs: dict[int, pilot.YearCatalog],
) -> dict[str, object]:
    rng = np.random.default_rng(409001)
    scene: dict[int, np.ndarray] = {}
    for year in pilot.YEARS:
        catalog = catalogs[year]
        mask = (
            np.abs(
                pilot.circular_delta(
                    catalog.solar_longitude,
                    10.0,
                )
            )
            <= pilot.WINDOW_HALF_WIDTH_DEG
        )
        indices = np.flatnonzero(mask)
        if len(indices) < EXTERNAL_PER_YEAR_EVENTS:
            raise RuntimeError(
                f"Only {len(indices)} events for {year} in the M2026-A1 control; "
                f"need {EXTERNAL_PER_YEAR_EVENTS}"
            )
        chosen = rng.choice(
            indices,
            size=EXTERNAL_PER_YEAR_EVENTS,
            replace=False,
        )
        scene[year] = catalog.raw_features[chosen].copy()

    evaluation = pilot.evaluate_prepared_scene(pilot.prepare_scene(scene))
    reference = pilot.m2026_reference_raw()
    distance = (
        math.inf
        if evaluation.localization_raw is None
        else pilot.raw_distance(evaluation.localization_raw, reference)
    )
    return {
        "per_year_events": EXTERNAL_PER_YEAR_EVENTS,
        "log_evalues": evaluation.log_evalues,
        "evalues": {
            method: float(math.exp(min(value, 200.0)))
            for method, value in evaluation.log_evalues.items()
        },
        "order_log_evalues": evaluation.order_log_evalues,
        "accepted_primary": evaluation.log_evalues[pilot.PRIMARY]
        >= pilot.LOG_THRESHOLD,
        "localization_raw": None
        if evaluation.localization_raw is None
        else evaluation.localization_raw.tolist(),
        "localization_radius": evaluation.localization_radius,
        "distance_to_reference": distance,
        "near_reference": distance <= pilot.M2026_DISTANCE,
        "reference_raw": reference.tolist(),
    }


def main() -> None:
    pilot.evaluate_m2026 = corrected_evaluate_m2026
    pilot.main()


if __name__ == "__main__":
    main()
