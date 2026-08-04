import type { FacialLandmarks, LandmarkId, Point2D } from "./landmarks.ts";

const IMAGE_SIZE = 1000;

type RawPoints = Partial<Record<LandmarkId, [number, number]>>;

function point(x: number, y: number): Point2D {
  return {
    x: (x + 0.5) * IMAGE_SIZE,
    y: y * IMAGE_SIZE,
    confidence: 1,
    source: "manual",
  };
}

function landmarks(view: "front" | "profile", raw: RawPoints): FacialLandmarks {
  const mapped: Partial<Record<LandmarkId, Point2D>> = {};
  for (const [id, value] of Object.entries(raw)) {
    if (!value) continue;
    mapped[id as LandmarkId] = point(value[0], value[1]);
  }

  return {
    view,
    imageWidth: IMAGE_SIZE,
    imageHeight: 1200,
    detectionConfidence: 1,
    poseWarnings: [],
    points: mapped,
  };
}

/** One internally consistent neutral frontal solution to Mog's v2 bands. */
export function referenceFrontLandmarks(): FacialLandmarks {
  const faceWidth = 0.78;
  const jawWidth = faceWidth / 1.25;
  const templeWidth = faceWidth * 0.84;
  const gonionY = 1 - (jawWidth / 2) / Math.tan(60 * Math.PI / 180);

  const pupilDistance = faceWidth * 0.47;
  const eyeWidth = pupilDistance / 2;
  const eyeHorizontal = eyeWidth * Math.cos(5 * Math.PI / 180);
  const eyeRise = eyeWidth * Math.sin(5 * Math.PI / 180);
  const innerX = eyeWidth / 2;
  const outerX = innerX + eyeHorizontal;
  const pupilX = pupilDistance / 2;
  const eyeY = 0.42;
  const eyeOpening = eyeWidth * 0.32;

  const browLength = faceWidth * 0.28;
  const browHorizontal = browLength * Math.cos(7 * Math.PI / 180);
  const browRise = browLength * Math.sin(7 * Math.PI / 180);
  const browMedialX = 0.07;
  const browMedialY = 0.36;

  const noseWidth = eyeWidth;
  const mouthWidth = noseWidth / 0.66;
  const stomionY = (0.666 + 0.5) / 1.5;
  const visibleLipHeight = 0.05;
  const upperShare = 0.58 / 1.58;
  const neckWidth = jawWidth * 0.74;

  return landmarks("front", {
    trichion: [0, 0],
    glabella: [0, 0.333],
    nasion: [0, 0.376],
    pronasale: [0, 0.63],
    subnasale: [0, 0.666],
    labialeSuperius: [0, stomionY - visibleLipHeight * upperShare],
    stomion: [0, stomionY],
    labialeInferius: [0, stomionY + visibleLipHeight * (1 - upperShare)],
    menton: [0, 1],
    gnathion: [0, 0.975],
    pogonion: [0, 0.92],

    leftZygion: [faceWidth / 2, 0.533],
    rightZygion: [-faceWidth / 2, 0.533],
    leftGonion: [jawWidth / 2, gonionY],
    rightGonion: [-jawWidth / 2, gonionY],
    leftFrontotemporale: [templeWidth / 2, 0.24],
    rightFrontotemporale: [-templeWidth / 2, 0.24],

    leftEndocanthion: [innerX, eyeY + eyeRise / 2],
    rightEndocanthion: [-innerX, eyeY + eyeRise / 2],
    leftExocanthion: [outerX, eyeY - eyeRise / 2],
    rightExocanthion: [-outerX, eyeY - eyeRise / 2],
    leftPupilCenter: [pupilX, eyeY],
    rightPupilCenter: [-pupilX, eyeY],
    leftSuperiorEyelid: [pupilX, eyeY - eyeOpening / 2],
    rightSuperiorEyelid: [-pupilX, eyeY - eyeOpening / 2],
    leftInferiorEyelid: [pupilX, eyeY + eyeOpening / 2],
    rightInferiorEyelid: [-pupilX, eyeY + eyeOpening / 2],

    leftEyebrowMedial: [browMedialX, browMedialY],
    rightEyebrowMedial: [-browMedialX, browMedialY],
    leftEyebrowLateral: [browMedialX + browHorizontal, browMedialY - browRise],
    rightEyebrowLateral: [-browMedialX - browHorizontal, browMedialY - browRise],
    leftEyebrowHigh: [pupilX, eyeY - eyeWidth * 0.42],
    rightEyebrowHigh: [-pupilX, eyeY - eyeWidth * 0.42],

    leftAlare: [noseWidth / 2, 0.658],
    rightAlare: [-noseWidth / 2, 0.658],
    leftCristaPhiltri: [0.024, 0.735],
    rightCristaPhiltri: [-0.024, 0.735],
    leftCheilion: [mouthWidth / 2, stomionY],
    rightCheilion: [-mouthWidth / 2, stomionY],

    leftTragion: [0.415, 0.535],
    rightTragion: [-0.415, 0.535],
    leftNeckBoundary: [neckWidth / 2, 1.08],
    rightNeckBoundary: [-neckWidth / 2, 1.08],
    midlineUpper: [0, 0.25],
    midlineLower: [0, 1],
  });
}

/**
 * Neutral profile geometry initialized from the Apache-2.0 Google GNM mean
 * head and minimally regularized into every scored Mog v2 comparison band.
 * This keeps the solved profile close to a coherent anatomical surface instead
 * of optimizing an unconstrained chain of independent 2D points.
 */
export function referenceProfileLandmarks(): FacialLandmarks {
  return landmarks("profile", {
    trichion: [0, 0],
    upperForehead: [0.03, 0.16],
    glabella: [0.00186, 0.26527],
    browRidge: [0.061, 0.285],
    nasion: [-0.01059, 0.32685],
    orbitale: [-0.05, 0.4],
    tragion: [-0.5, 0.4],

    pronasale: [0.1488, 0.56235],
    columella: [0.1045, 0.59683],
    subnasale: [0.04588, 0.60613],
    alare: [-0.00137, 0.62048],
    labialeSuperius: [0.06528, 0.713],
    stomion: [0.05639, 0.75662],
    labialeInferius: [0.05013, 0.80709],
    mentolabialSulcus: [0.00617, 0.87921],

    softTissuePogonion: [0.02255, 0.94177],
    pogonion: [0.02255, 0.94177],
    gnathion: [0.01, 0.98],
    menton: [0, 1],
    gonion: [-0.35752, 0.88602],
    ramusPoint: [-0.45641, 0.68827],
    cervicalPoint: [-0.097438, 0.975302],
    throatPoint: [-0.185793, 1.105199],
    cheekProjection: [0, 0.48],
  });
}

export const referenceFaceViews = {
  front: referenceFrontLandmarks,
  profile: referenceProfileLandmarks,
} as const;
