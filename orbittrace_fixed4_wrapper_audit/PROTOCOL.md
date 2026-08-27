# OrbitTrace fixed4 wrapper-saturation audit

## Question

Did the broad ranked-quartet catalogue wrapper provide a fair negative test of an episodic sparse stream, or did its preserved ranking saturate with persistent all-year families before shorter-lived recurrent families could enter the reveal set?

This is an artifact-only diagnostic. It does not rerun either detector application, alter a family, rescore a quartet, use an alternate OrbitTrace match, or authorize a new claim by itself.

## Frozen evidence

- broad ranked-quartet final artifact: `8957230278`, ZIP SHA-256 `2ee3d5c9edf299c0f9ea69b2d6254d7918e0aa659f8cc2c659bb99ff2dfc0d17`;
- calibrated component-family blind scan artifact: `8958042095`, ZIP SHA-256 `3ce72dde553cf58c6d4b9e734c29558a0f2bbefee664ba98189f4e90e821c596`;
- calibrated reveal artifact: `8958194010`, ZIP SHA-256 `74c95a3fd59650126a2a298fc1bab5cc055caa91bff2feae6c9256521fdc00aa`.

## Fixed checks

1. For every broad-wrapper threshold (`1.5`, `2.0`, `2.5`), count support years for all preserved top-5,000 families.
2. Reproduce the broad canonical availability by year and count years containing at least four canonical events, the minimum required to form a pure canonical quartet.
3. Verify the calibrated wrapper's selected family, blind rank, event count, overlap, precision, and year support.
4. Compare the calibrated family's year support with the minimum support represented anywhere in the broad top-5,000 lists.
5. Classify:
   - `PERSISTENCE_RANKING_SATURATION_CONFIRMED` if every broad top-5,000 family at every threshold has support across all eight catalogue years and the calibrated recovered family has fewer than eight years;
   - otherwise `NO_COMPLETE_PERSISTENCE_SATURATION`.

## Interpretation boundary

A confirmed saturation result does not erase the preregistered broad-wrapper negative outcome. It shows that the negative outcome is specifically evidence against a persistence-first recurrence wrapper, not a clean independent refutation of the fixed4 detector's ability to recover episodic streams. It authorizes development of a generic support-normalized wrapper only on non-OrbitTrace showers with the `20°–55°` interval excluded before all labels and endpoints.