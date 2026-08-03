"use client";

import { useMemo, useState } from "react";
import { calculateAnalysisReport } from "@/lib/analysis/calculate-report";
import type { FacialLandmarks, LandmarkId, Point2D } from "@/lib/analysis/landmarks";
import {
  referenceFrontLandmarks,
  referenceProfileLandmarks,
} from "@/lib/analysis/reference-face-geometry";

type FaceView = "front" | "profile";
type RenderMode = "structure" | "rendered";
type SvgPoint = { x: number; y: number };

function requiredPoint(landmarks: FacialLandmarks, id: LandmarkId): Point2D {
  const value = landmarks.points[id];
  if (!value) throw new Error(`Reference face is missing ${id}`);
  return value;
}

function frontMap(point: Point2D): SvgPoint {
  return { x: 300 + (point.x - 500) * 0.46, y: 50 + point.y * 0.46 };
}

function profileMap(point: Point2D): SvgPoint {
  return { x: 120 + (point.x - 150) * 0.66, y: 45 + point.y * 0.46 };
}

function eyePath(inner: SvgPoint, outer: SvgPoint, height: number): string {
  const centerX = (inner.x + outer.x) / 2;
  const upperY = Math.min(inner.y, outer.y) - height * 0.55;
  const lowerY = Math.max(inner.y, outer.y) + height * 0.43;
  return `M ${inner.x} ${inner.y} Q ${centerX} ${upperY} ${outer.x} ${outer.y} Q ${centerX} ${lowerY} ${inner.x} ${inner.y} Z`;
}

function FrontReference({ mode, landmarks }: { mode: RenderMode; landmarks: FacialLandmarks }) {
  const q = (id: LandmarkId) => frontMap(requiredPoint(landmarks, id));
  const trichion = q("trichion");
  const glabella = q("glabella");
  const subnasale = q("subnasale");
  const menton = q("menton");
  const leftTemple = q("leftFrontotemporale");
  const rightTemple = q("rightFrontotemporale");
  const leftCheek = q("leftZygion");
  const rightCheek = q("rightZygion");
  const leftJaw = q("leftGonion");
  const rightJaw = q("rightGonion");
  const leftTragion = q("leftTragion");
  const rightTragion = q("rightTragion");

  const leftInner = q("leftEndocanthion");
  const leftOuter = q("leftExocanthion");
  const rightInner = q("rightEndocanthion");
  const rightOuter = q("rightExocanthion");
  const leftPupil = q("leftPupilCenter");
  const rightPupil = q("rightPupilCenter");
  const eyeHeight = Math.abs(q("leftInferiorEyelid").y - q("leftSuperiorEyelid").y);
  const leftEye = eyePath(leftInner, leftOuter, eyeHeight);
  const rightEye = eyePath(rightInner, rightOuter, eyeHeight);

  const leftBrowMedial = q("leftEyebrowMedial");
  const leftBrowLateral = q("leftEyebrowLateral");
  const leftBrowHigh = q("leftEyebrowHigh");
  const rightBrowMedial = q("rightEyebrowMedial");
  const rightBrowLateral = q("rightEyebrowLateral");
  const rightBrowHigh = q("rightEyebrowHigh");
  const leftAlare = q("leftAlare");
  const rightAlare = q("rightAlare");
  const leftMouth = q("leftCheilion");
  const rightMouth = q("rightCheilion");
  const upperLip = q("labialeSuperius");
  const stomion = q("stomion");
  const lowerLip = q("labialeInferius");

  const facePath = `M ${leftTemple.x} ${leftTemple.y}
    C ${leftTemple.x + 5} ${leftTemple.y - 51}, ${trichion.x + 72} ${trichion.y + 10}, ${trichion.x} ${trichion.y}
    C ${trichion.x - 72} ${trichion.y + 10}, ${rightTemple.x - 5} ${rightTemple.y - 51}, ${rightTemple.x} ${rightTemple.y}
    C ${rightTemple.x - 11} ${rightTemple.y + 48}, ${rightCheek.x - 3} ${rightCheek.y - 45}, ${rightCheek.x} ${rightCheek.y}
    C ${rightCheek.x + 2} ${subnasale.y + 49}, ${rightJaw.x - 8} ${rightJaw.y - 27}, ${rightJaw.x} ${rightJaw.y}
    C ${rightJaw.x + 23} ${menton.y - 30}, ${menton.x - 48} ${menton.y - 3}, ${menton.x} ${menton.y}
    C ${menton.x + 48} ${menton.y - 3}, ${leftJaw.x - 23} ${menton.y - 30}, ${leftJaw.x} ${leftJaw.y}
    C ${leftJaw.x + 8} ${leftJaw.y - 27}, ${leftCheek.x - 2} ${subnasale.y + 49}, ${leftCheek.x} ${leftCheek.y}
    C ${leftCheek.x + 3} ${leftCheek.y - 45}, ${leftTemple.x - 11} ${leftTemple.y + 48}, ${leftTemple.x} ${leftTemple.y} Z`;

  const hairPath = `M ${leftTemple.x} ${leftTemple.y}
    C ${leftTemple.x + 10} ${leftTemple.y - 65}, ${trichion.x + 94} 20, ${trichion.x} 16
    C ${trichion.x - 94} 20, ${rightTemple.x - 10} ${rightTemple.y - 65}, ${rightTemple.x} ${rightTemple.y}
    Q ${trichion.x} ${trichion.y + 22} ${leftTemple.x} ${leftTemple.y} Z`;

  const neckLeft = menton.x - 56;
  const neckRight = menton.x + 56;
  const neckPath = `M ${menton.x - 52} ${menton.y - 10}
    C ${neckLeft} ${menton.y + 20}, ${neckLeft} 564, ${neckLeft - 12} 577
    L ${neckRight + 12} 577
    C ${neckRight} 564, ${neckRight} ${menton.y + 20}, ${menton.x + 52} ${menton.y - 10} Z`;
  const shoulders = "M 72 620 C 130 574, 218 570, 244 555 C 267 581, 333 581, 356 555 C 382 570, 470 574, 528 620 Z";

  const upperLipPath = `M ${leftMouth.x} ${stomion.y}
    Q ${stomion.x - 25} ${upperLip.y - 2} ${upperLip.x} ${upperLip.y}
    Q ${stomion.x + 25} ${upperLip.y - 2} ${rightMouth.x} ${stomion.y}
    Q ${stomion.x} ${stomion.y + 1.5} ${leftMouth.x} ${stomion.y} Z`;
  const lowerLipPath = `M ${leftMouth.x} ${stomion.y}
    Q ${lowerLip.x} ${lowerLip.y + 3} ${rightMouth.x} ${stomion.y}
    Q ${stomion.x} ${stomion.y + 1.5} ${leftMouth.x} ${stomion.y} Z`;

  const structureIds: LandmarkId[] = [
    "trichion", "glabella", "nasion", "subnasale", "menton",
    "leftZygion", "rightZygion", "leftGonion", "rightGonion",
    "leftEndocanthion", "leftExocanthion", "rightEndocanthion", "rightExocanthion",
    "leftPupilCenter", "rightPupilCenter", "leftAlare", "rightAlare",
    "leftCheilion", "rightCheilion",
  ];

  return (
    <svg viewBox="0 0 600 620" role="img" aria-label={`Front target face in ${mode} mode`} className="h-auto w-full">
      <defs>
        <linearGradient id="verifiedFrontClay" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f0ebe4" />
          <stop offset="55%" stopColor="#d8cec4" />
          <stop offset="100%" stopColor="#baa99c" />
        </linearGradient>
        <linearGradient id="verifiedFrontHair" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#343434" />
          <stop offset="100%" stopColor="#59544f" />
        </linearGradient>
        <radialGradient id="verifiedFrontLight" cx="45%" cy="30%" r="75%">
          <stop offset="0%" stopColor="#fff" stopOpacity="0.45" />
          <stop offset="70%" stopColor="#fff" stopOpacity="0" />
          <stop offset="100%" stopColor="#6b5a50" stopOpacity="0.14" />
        </radialGradient>
        <filter id="verifiedFrontBlur" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="9" /></filter>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={shoulders} fill="#bbb4ae" />
          <path d={neckPath} fill="url(#verifiedFrontClay)" />
          <ellipse cx={leftTragion.x - 1} cy={leftTragion.y + 14} rx="14" ry="34" fill="#d2c6bb" />
          <ellipse cx={rightTragion.x + 1} cy={rightTragion.y + 14} rx="14" ry="34" fill="#d2c6bb" />
          <path d={facePath} fill="url(#verifiedFrontClay)" stroke="#84786f" strokeWidth="0.8" />
          <path d={hairPath} fill="url(#verifiedFrontHair)" />
          <path d={facePath} fill="url(#verifiedFrontLight)" />

          <ellipse cx={leftPupil.x - 13} cy={leftPupil.y + 67} rx="44" ry="28" fill="#80685c" opacity="0.07" filter="url(#verifiedFrontBlur)" />
          <ellipse cx={rightPupil.x + 13} cy={rightPupil.y + 67} rx="44" ry="28" fill="#80685c" opacity="0.07" filter="url(#verifiedFrontBlur)" />
          <path d={leftEye} fill="#fbfaf8" stroke="#4b4947" strokeWidth="1.2" />
          <path d={rightEye} fill="#fbfaf8" stroke="#4b4947" strokeWidth="1.2" />
          <ellipse cx={leftPupil.x} cy={leftPupil.y - 1} rx="8" ry="9.5" fill="#74716a" />
          <ellipse cx={rightPupil.x} cy={rightPupil.y - 1} rx="8" ry="9.5" fill="#74716a" />
          <circle cx={leftPupil.x} cy={leftPupil.y} r="3.9" fill="#282725" />
          <circle cx={rightPupil.x} cy={rightPupil.y} r="3.9" fill="#282725" />
          <circle cx={leftPupil.x - 2.2} cy={leftPupil.y - 3.5} r="1.45" fill="white" />
          <circle cx={rightPupil.x - 2.2} cy={rightPupil.y - 3.5} r="1.45" fill="white" />

          <path d={`M ${leftBrowLateral.x} ${leftBrowLateral.y} Q ${leftBrowHigh.x} ${leftBrowHigh.y - 3} ${leftBrowMedial.x} ${leftBrowMedial.y}`} fill="none" stroke="#474440" strokeWidth="4.8" strokeLinecap="round" />
          <path d={`M ${rightBrowMedial.x} ${rightBrowMedial.y} Q ${rightBrowHigh.x} ${rightBrowHigh.y - 3} ${rightBrowLateral.x} ${rightBrowLateral.y}`} fill="none" stroke="#474440" strokeWidth="4.8" strokeLinecap="round" />

          <path d={`M ${glabella.x - 4} ${glabella.y + 17} C ${glabella.x - 10} ${leftPupil.y + 36}, ${glabella.x - 12} ${subnasale.y - 25}, ${leftAlare.x + 7} ${leftAlare.y - 6}`} fill="none" stroke="#8e7a6e" strokeWidth="1.2" strokeLinecap="round" opacity="0.62" />
          <path d={`M ${glabella.x + 4} ${glabella.y + 17} C ${glabella.x + 8} ${rightPupil.y + 36}, ${glabella.x + 12} ${subnasale.y - 25}, ${rightAlare.x - 7} ${rightAlare.y - 6}`} fill="none" stroke="#fff" strokeWidth="1.3" strokeLinecap="round" opacity="0.38" />
          <path d={`M ${leftAlare.x} ${leftAlare.y} Q ${subnasale.x - 17} ${subnasale.y + 5} ${subnasale.x} ${subnasale.y + 2} Q ${subnasale.x + 17} ${subnasale.y + 5} ${rightAlare.x} ${rightAlare.y}`} fill="none" stroke="#74665d" strokeWidth="1.2" />
