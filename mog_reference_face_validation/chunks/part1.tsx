"use client";

import { useMemo, useState } from "react";
import { getReferenceBand } from "@/lib/analysis/reference-bands.ts";

type FaceView = "front" | "profile";
type RenderMode = "structure" | "rendered";
type Point = { x: number; y: number };
type TargetMetric = {
  id: string;
  label: string;
  unit: "ratio" | "degrees" | "percent" | "normalized-distance";
};

const FRONT_TARGETS: TargetMetric[] = [
  { id: "front-upper-third", label: "Upper third", unit: "ratio" },
  { id: "front-middle-third", label: "Middle third", unit: "ratio" },
  { id: "front-lower-third", label: "Lower third", unit: "ratio" },
  { id: "front-bizygomatic-height", label: "Face width / height", unit: "ratio" },
  { id: "front-bizygomatic-bigonial", label: "Cheek / jaw width", unit: "ratio" },
  { id: "front-bitemporal-bizygomatic", label: "Temple / cheek width", unit: "ratio" },
  { id: "front-intercanthal-eye", label: "Eye spacing", unit: "ratio" },
  { id: "front-interpupil-face", label: "Pupil spacing / face", unit: "ratio" },
  { id: "front-eye-aspect", label: "Eye aspect", unit: "ratio" },
  { id: "front-average-canthal", label: "Canthal tilt", unit: "degrees" },
  { id: "front-nose-intercanthal", label: "Nose / inner-eye gap", unit: "ratio" },
  { id: "front-nose-mouth", label: "Nose / mouth width", unit: "ratio" },
  { id: "front-mouth-interpupil", label: "Mouth / pupil spacing", unit: "ratio" },
  { id: "front-lip-ratio", label: "Upper / lower lip", unit: "ratio" },
  { id: "front-jaw-taper", label: "Jaw taper", unit: "degrees" },
];

const PROFILE_TARGETS: TargetMetric[] = [
  { id: "profile-forehead-slope", label: "Forehead slope", unit: "degrees" },
  { id: "profile-nasofrontal", label: "Nasofrontal angle", unit: "degrees" },
  { id: "profile-dorsum-angle", label: "Nasal dorsum", unit: "degrees" },
  { id: "profile-tip-rotation", label: "Tip rotation", unit: "degrees" },
  { id: "profile-nasolabial", label: "Nasolabial angle", unit: "degrees" },
  { id: "profile-goode", label: "Goode projection", unit: "ratio" },
  { id: "profile-nose-length", label: "Nose / profile height", unit: "ratio" },
  { id: "profile-total-convexity", label: "Total convexity", unit: "degrees" },
  { id: "profile-upper-e-line", label: "Upper lip to E-line", unit: "normalized-distance" },
  { id: "profile-lower-e-line", label: "Lower lip to E-line", unit: "normalized-distance" },
  { id: "profile-h-angle", label: "H-angle", unit: "degrees" },
  { id: "profile-mentolabial", label: "Mentolabial angle", unit: "degrees" },
  { id: "profile-z-angle", label: "Z-angle", unit: "degrees" },
  { id: "profile-mandibular-plane", label: "Mandibular plane", unit: "degrees" },
  { id: "profile-gonial", label: "Gonial angle", unit: "degrees" },
];

function target(id: string, fallback: number): number {
  const band = getReferenceBand(id, "neutral");
  return band?.center ?? (band ? (band.low + band.high) / 2 : fallback);
}

function targetLabel(metric: TargetMetric): string {
  const value = target(metric.id, 0);
  if (metric.unit === "degrees") return `${Math.round(value)}°`;
  if (metric.unit === "percent") return `${value.toFixed(1)}%`;
  if (metric.unit === "normalized-distance") return value.toFixed(3);
  return value.toFixed(2);
}

function clamp(value: number, low: number, high: number): number {
  return Math.max(low, Math.min(high, value));
}

function polar(origin: Point, length: number, degrees: number): Point {
  const radians = (degrees * Math.PI) / 180;
  return {
    x: origin.x + Math.cos(radians) * length,
    y: origin.y + Math.sin(radians) * length,
  };
}

function eyePath(inner: Point, outer: Point, height: number): string {
  const midX = (inner.x + outer.x) / 2;
  const upperY = Math.min(inner.y, outer.y) - height * 0.6;
  const lowerY = Math.max(inner.y, outer.y) + height * 0.5;
  return `M ${inner.x} ${inner.y} Q ${midX} ${upperY} ${outer.x} ${outer.y} Q ${midX} ${lowerY} ${inner.x} ${inner.y} Z`;
}

function frontGeometry() {
  const centerX = 300;
  const hairlineY = 92;
  const chinY = 536;
  const faceHeight = chinY - hairlineY;
  const cheekWidth = clamp(faceHeight * target("front-bizygomatic-height", 0.78), 336, 360);
  const jawWidth = clamp(cheekWidth / target("front-bizygomatic-bigonial", 1.25), 264, 294);
  const templeWidth = clamp(cheekWidth * target("front-bitemporal-bizygomatic", 0.84), 282, 312);

  const upper = target("front-upper-third", 0.333);
  const middle = target("front-middle-third", 0.333);
  const lower = target("front-lower-third", 0.34);
  const total = upper + middle + lower;
  const glabellaY = hairlineY + faceHeight * upper / total;
  const subnasaleY = glabellaY + faceHeight * middle / total;

  const pupilDistance = cheekWidth * target("front-interpupil-face", 0.47);
  const spacing = target("front-intercanthal-eye", 1);
  const eyeWidth = pupilDistance / (1 + spacing);
  const innerGap = eyeWidth * spacing;
  const eyeHeight = eyeWidth * target("front-eye-aspect", 0.32);
  const eyeY = glabellaY + (subnasaleY - glabellaY) * 0.32;
  const canthalRise = Math.tan(target("front-average-canthal", 5) * Math.PI / 180) * eyeWidth;

  const noseFromEyes = innerGap * target("front-nose-intercanthal", 1);
  const mouthFromPupils = pupilDistance * target("front-mouth-interpupil", 0.94);
  const mouthFromNose = noseFromEyes / target("front-nose-mouth", 0.66);
  const mouthWidth = mouthFromPupils * 0.68 + mouthFromNose * 0.32;
  const noseWidth = noseFromEyes * 0.72 + mouthWidth * target("front-nose-mouth", 0.66) * 0.28;
  const mouthY = subnasaleY + (chinY - subnasaleY) * 0.36;
  const lipHeight = faceHeight * 0.044;
  const upperLipShare = target("front-lip-ratio", 0.58) / (1 + target("front-lip-ratio", 0.58));

  return {
    centerX, hairlineY, chinY, glabellaY, subnasaleY,
    cheekWidth, jawWidth, templeWidth,
    pupilDistance, eyeWidth, innerGap, eyeHeight, eyeY, canthalRise,
    noseWidth, mouthWidth, mouthY, lipHeight, upperLipShare,
  };
}

function profileGeometry() {
  const trichion: Point = { x: 286, y: 83 };
  const chinY = 501;
  const profileHeight = chinY - trichion.y;
  const foreheadSlope = target("profile-forehead-slope", 16);
  const upperForehead: Point = {
    x: trichion.x + Math.tan(foreheadSlope * Math.PI / 180) * 52,
    y: 154,
  };
  const glabella: Point = { x: upperForehead.x + 16, y: 205 };
  const nasion: Point = { x: glabella.x - 6, y: 234 };
  const noseLength = clamp(profileHeight * target("profile-nose-length", 0.3) * 0.9, 108, 119);
  const dorsumAngle = clamp(target("profile-dorsum-angle", 30), 27, 33);
  const pronasale = polar(nasion, noseLength, dorsumAngle);

  // Screen coordinates increase downward. A natural columella runs down and back from the tip.
  const tipRotation = target("profile-tip-rotation", 100);
  const tipToColumellaAngle = 135 + (tipRotation - 100) * 0.2;
  const columella = polar(pronasale, 34, tipToColumellaAngle);
  const subnasale: Point = { x: columella.x - 12, y: columella.y + 13 };
  const upperLip: Point = { x: subnasale.x + 6, y: subnasale.y + 34 };
  const stomion: Point = { x: upperLip.x - 3, y: upperLip.y + 14 };
  const lowerLip: Point = { x: upperLip.x + 5, y: stomion.y + 16 };
  const sulcus: Point = { x: lowerLip.x - 14, y: lowerLip.y + 27 };
  const pogonion: Point = { x: upperLip.x + 8, y: chinY - 47 };
  const menton: Point = { x: pogonion.x - 27, y: chinY };

  const mandibularAngle = clamp(target("profile-mandibular-plane", 23), 18, 27);
  const gonion = polar(menton, 132, 180 + mandibularAngle);
  const ramus: Point = { x: gonion.x - 9, y: gonion.y - 118 };
  const tragion: Point = { x: ramus.x + 7, y: 249 };
  const orbitale: Point = { x: nasion.x - 4, y: tragion.y };
  const cheek: Point = { x: orbitale.x + 18, y: orbitale.y + 43 };
  const neckFront: Point = { x: menton.x - 10, y: 558 };
  const neckBack: Point = { x: gonion.x - 58, y: 558 };
  const skullBack: Point = { x: 178, y: 181 };
  const crown: Point = { x: 221, y: 57 };

  return {
    trichion, upperForehead, glabella, nasion, pronasale, columella,
    subnasale, upperLip, stomion, lowerLip, sulcus, pogonion, menton,
    gonion, ramus, tragion, orbitale, cheek, neckFront, neckBack,
    skullBack, crown,
  };
}

function FrontFace({ mode }: { mode: RenderMode }) {
  const g = useMemo(frontGeometry, []);
  const leftCheek = g.centerX - g.cheekWidth / 2;
  const rightCheek = g.centerX + g.cheekWidth / 2;
  const leftJaw = g.centerX - g.jawWidth / 2;
  const rightJaw = g.centerX + g.jawWidth / 2;
  const leftTemple = g.centerX - g.templeWidth / 2;
  const rightTemple = g.centerX + g.templeWidth / 2;
  const leftPupil = g.centerX - g.pupilDistance / 2;
  const rightPupil = g.centerX + g.pupilDistance / 2;
