type ReferenceBand = {
  metricId: string;
  profile: "neutral";
  low: number;
  high: number;
  center?: number;
};

const neutral: Record<string, [number, number, number?]> = {
  "front-upper-third": [0.29, 0.37, 0.333],
  "front-middle-third": [0.29, 0.37, 0.333],
  "front-lower-third": [0.29, 0.39, 0.34],
  "front-bizygomatic-height": [0.68, 0.88, 0.78],
  "front-bizygomatic-bigonial": [1.12, 1.42, 1.25],
  "front-bitemporal-bizygomatic": [0.74, 0.92, 0.84],
  "front-eye-aspect": [0.24, 0.42, 0.32],
  "front-intercanthal-eye": [0.82, 1.18, 1],
  "front-interpupil-face": [0.42, 0.52, 0.47],
  "front-average-canthal": [1, 10, 5],
  "front-eyebrow-height": [0.28, 0.58, 0.42],
  "front-nose-intercanthal": [0.82, 1.2, 1],
  "front-nose-mouth": [0.56, 0.76, 0.66],
  "front-mouth-interpupil": [0.82, 1.08, 0.94],
  "front-lip-ratio": [0.42, 0.78, 0.58],
  "front-jaw-taper": [62, 88, 75],
  "profile-forehead-slope": [8, 24, 16],
  "profile-nasofrontal": [125, 145, 135],
  "profile-dorsum-angle": [23, 38, 30],
  "profile-tip-rotation": [88, 112, 100],
  "profile-nasolabial": [88, 112, 100],
  "profile-goode": [0.5, 0.67, 0.58],
  "profile-nose-length": [0.24, 0.36, 0.3],
  "profile-total-convexity": [160, 178, 169],
  "profile-upper-e-line": [-0.055, 0.015, -0.02],
  "profile-lower-e-line": [-0.035, 0.025, -0.005],
  "profile-h-angle": [7, 18, 12],
  "profile-mentolabial": [100, 135, 118],
  "profile-z-angle": [68, 82, 75],
  "profile-mandibular-plane": [15, 32, 23],
  "profile-gonial": [110, 135, 122],
};

export function getReferenceBand(metricId: string, profile: "neutral"): ReferenceBand | undefined {
  const tuple = neutral[metricId];
  if (!tuple) return undefined;
  return {
    metricId,
    profile,
    low: tuple[0],
    high: tuple[1],
    center: tuple[2],
  };
}
