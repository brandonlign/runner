export type LandmarkId = string;

export type Point2D = {
  x: number;
  y: number;
  confidence: number;
  source: "manual" | "detected" | "estimated";
};

export type FacialLandmarks = {
  view: "front" | "profile";
  imageWidth: number;
  imageHeight: number;
  detectionConfidence: number;
  poseWarnings: string[];
  points: Partial<Record<LandmarkId, Point2D>>;
};
