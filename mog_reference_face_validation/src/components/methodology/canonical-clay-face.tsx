import type { FacialLandmarks } from "@/lib/analysis/landmarks";
import { GNM_FRONT_WEBP, GNM_PROFILE_WEBP } from "./gnm-clay-renders";

type FaceView = "front" | "profile";

/**
 * Reproducible full-resolution Google GNM clay snapshot. The image is
 * illustrative only; all scoring continues to use the separate canonical
 * semantic landmarks shown in structure mode.
 */
export function CanonicalClayFace({ view }: { view: FaceView; landmarks: FacialLandmarks }) {
  const href = view === "front" ? GNM_FRONT_WEBP : GNM_PROFILE_WEBP;
  return (
    <g aria-label={`Google GNM neutral clay ${view} illustration`}>
      <image href={href} x="0" y="-2" width="600" height="624" preserveAspectRatio="xMidYMid meet" />
    </g>
  );
}
