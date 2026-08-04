/**
 * Deterministic full-resolution clay snapshots rendered from the Apache-2.0
 * Google GNM v3.0 neutral head. They are fitted to the frozen
 * `gnm-neutral-v2` reference geometry, but remain illustrative: Mog always
 * recomputes measurements from `reference-face-geometry.ts`, never pixels.
 */
import { GNM_CLAY_FRONT_1 } from "./gnm-clay-front-1";
import { GNM_CLAY_FRONT_2 } from "./gnm-clay-front-2";
import { GNM_CLAY_FRONT_3 } from "./gnm-clay-front-3";
import { GNM_CLAY_FRONT_4 } from "./gnm-clay-front-4";
import { GNM_CLAY_FRONT_5 } from "./gnm-clay-front-5";
import { GNM_CLAY_PROFILE_1 } from "./gnm-clay-profile-1";
import { GNM_CLAY_PROFILE_2 } from "./gnm-clay-profile-2";
import { GNM_CLAY_PROFILE_3 } from "./gnm-clay-profile-3";

export const GNM_REFERENCE_GEOMETRY_REVISION = "gnm-neutral-v2" as const;

const GNM_FRONT_BASE64 =
  GNM_CLAY_FRONT_1 +
  GNM_CLAY_FRONT_2 +
  GNM_CLAY_FRONT_3 +
  GNM_CLAY_FRONT_4 +
  GNM_CLAY_FRONT_5;

const GNM_PROFILE_BASE64 =
  GNM_CLAY_PROFILE_1 +
  GNM_CLAY_PROFILE_2 +
  GNM_CLAY_PROFILE_3;

export const GNM_FRONT_WEBP = `data:image/webp;base64,${GNM_FRONT_BASE64}`;
export const GNM_PROFILE_WEBP = `data:image/webp;base64,${GNM_PROFILE_BASE64}`;
