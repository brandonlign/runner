import type { FacialLandmarks } from "@/lib/analysis/landmarks";
import {
  GNM_FRONT_WEBP,
  GNM_PROFILE_WEBP,
  GNM_REFERENCE_GEOMETRY_REVISION,
} from "./gnm-clay-renders";

type FaceView = "front" | "profile";

/**
 * Full-resolution neutral Google GNM clay snapshot. It is illustrative only;
 * all scoring continues to use the separate canonical semantic landmarks
 * shown in structure mode.
 */
export function CanonicalClayFace({
  view,
  landmarks,
}: {
  view: FaceView;
  landmarks: FacialLandmarks;
}) {
  const href = view === "front" ? GNM_FRONT_WEBP : GNM_PROFILE_WEBP;
  return (
    <g
      aria-label={`Google GNM neutral clay ${view} illustration`}
      data-geometry-revision={GNM_REFERENCE_GEOMETRY_REVISION}
      data-landmark-view={landmarks.view}
    >
      <image
        href={href}
        x="0"
        y="0"
        width="600"
        height="620"
        preserveAspectRatio="xMidYMid meet"
      />
    </g>
  );
}
