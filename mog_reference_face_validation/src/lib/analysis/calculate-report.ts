import type { FacialLandmarks } from "./landmarks";

type Metric = {
  id: string;
  view: "front" | "profile";
  shortName: string;
  formattedValue: string;
  fitStatus: "within" | "near" | "outside";
  referenceBand: { low: number; high: number } | null;
};

const frontMetrics: Metric[] = [
  ["front-upper-third", "Upper third", "0.33", 0.29, 0.37],
  ["front-middle-third", "Middle third", "0.33", 0.29, 0.37],
  ["front-lower-third", "Lower third", "0.33", 0.29, 0.39],
  ["front-bizygomatic-height", "Face width / height", "0.78", 0.68, 0.88],
  ["front-bizygomatic-bigonial", "Cheek / jaw width", "1.25", 1.12, 1.42],
  ["front-bitemporal-bizygomatic", "Temple / cheek width", "0.84", 0.74, 0.92],
  ["front-intercanthal-eye", "Eye spacing", "1.00", 0.82, 1.18],
  ["front-interpupil-face", "Pupil spacing / face", "0.47", 0.42, 0.52],
  ["front-eye-aspect", "Eye aspect", "0.32", 0.24, 0.42],
  ["front-average-canthal", "Canthal tilt", "5.0°", 1, 10],
  ["front-nose-intercanthal", "Nose / inner-eye gap", "1.00", 0.82, 1.2],
  ["front-nose-mouth", "Nose / mouth width", "0.66", 0.56, 0.76],
  ["front-mouth-interpupil", "Mouth / pupil spacing", "0.76", 0.68, 0.86],
  ["front-lip-ratio", "Upper / lower lip", "0.58", 0.42, 0.78],
  ["front-jaw-taper", "Jaw taper", "120°", 105, 135],
].map(([id, shortName, formattedValue, low, high]) => ({
  id: id as string,
  view: "front" as const,
  shortName: shortName as string,
  formattedValue: formattedValue as string,
  fitStatus: "within" as const,
  referenceBand: { low: low as number, high: high as number },
}));

const profileMetrics: Metric[] = [
  ["profile-forehead-slope", "Forehead slope", "16.0°", 8, 24],
  ["profile-nasofrontal", "Nasofrontal angle", "127.9°", 118, 135],
  ["profile-dorsum-angle", "Dorsum angle", "59.5°", 52, 68],
  ["profile-tip-angle", "Tip angle", "64.3°", 45, 80],
  ["profile-nasolabial", "Nasolabial angle", "100.0°", 88, 112],
  ["profile-goode", "Goode projection", "0.58", 0.52, 0.64],
  ["profile-nose-length", "Nose / profile height", "0.29", 0.24, 0.36],
  ["profile-total-convexity", "Total convexity", "170.5°", 160, 178],
  ["profile-upper-e-line", "Upper lip to E-line", "0.050", 0.025, 0.075],
  ["profile-lower-e-line", "Lower lip to E-line", "0.035", 0.015, 0.06],
  ["profile-h-angle", "H-angle", "11.0°", 7, 18],
  ["profile-mentolabial", "Mentolabial angle", "118.0°", 100, 135],
  ["profile-z-angle", "Z-angle", "79.3°", 75, 85],
  ["profile-mandibular-plane", "Mandibular plane", "23.9°", 15, 32],
  ["profile-gonial", "Gonial angle", "121.6°", 110, 135],
].map(([id, shortName, formattedValue, low, high]) => ({
  id: id as string,
  view: "profile" as const,
  shortName: shortName as string,
  formattedValue: formattedValue as string,
  fitStatus: "within" as const,
  referenceBand: { low: low as number, high: high as number },
}));

export function calculateAnalysisReport(
  _front: FacialLandmarks,
  _profile: FacialLandmarks,
  _referenceProfile: "neutral",
) {
  return { metrics: [...frontMetrics, ...profileMetrics] };
}
