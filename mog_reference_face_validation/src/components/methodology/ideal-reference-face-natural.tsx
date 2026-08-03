"use client";

import { useMemo, useState } from "react";
import { getReferenceBand } from "@/lib/analysis/reference-bands.ts";

type FaceView = "front" | "profile";
type RenderMode = "structure" | "rendered";
type Point = { x: number; y: number };
type TargetMetric = {
  id: string;
  label: string;
  unit: "ratio" | "degrees" | "normalized-distance";
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

function label(metric: TargetMetric): string {
  const value = target(metric.id, 0);
  if (metric.unit === "degrees") return `${Math.round(value)}°`;
  if (metric.unit === "normalized-distance") return value.toFixed(3);
  return value.toFixed(2);
}

function clamp(value: number, low: number, high: number): number {
  return Math.max(low, Math.min(high, value));
}

function frontGeometry() {
  const centerX = 300;
  const hairlineY = 104;
  const chinY = 526;
  const faceHeight = chinY - hairlineY;
  const cheekWidth = clamp(faceHeight * target("front-bizygomatic-height", 0.78), 324, 340);
  const jawWidth = clamp(cheekWidth / target("front-bizygomatic-bigonial", 1.25), 256, 278);
  const templeWidth = clamp(cheekWidth * target("front-bitemporal-bizygomatic", 0.84), 276, 292);

  const upper = target("front-upper-third", 0.333);
  const middle = target("front-middle-third", 0.333);
  const lower = target("front-lower-third", 0.34);
  const total = upper + middle + lower;
  const glabellaY = hairlineY + faceHeight * upper / total;
  const subnasaleY = glabellaY + faceHeight * middle / total;

  const pupilDistance = cheekWidth * target("front-interpupil-face", 0.47);
  const eyeSpacing = target("front-intercanthal-eye", 1);
  const eyeWidth = pupilDistance / (1 + eyeSpacing);
  const innerGap = eyeWidth * eyeSpacing;
  const eyeHeight = eyeWidth * target("front-eye-aspect", 0.32);
  const eyeY = glabellaY + (subnasaleY - glabellaY) * 0.24;
  const rise = Math.tan(target("front-average-canthal", 5) * Math.PI / 180) * eyeWidth;

  const noseWidthA = innerGap * target("front-nose-intercanthal", 1);
  const mouthWidthA = pupilDistance * target("front-mouth-interpupil", 0.94);
  const mouthWidthB = noseWidthA / target("front-nose-mouth", 0.66);
  const mouthWidth = mouthWidthA * 0.7 + mouthWidthB * 0.3;
  const noseWidth = noseWidthA * 0.72 + mouthWidth * target("front-nose-mouth", 0.66) * 0.28;
  const mouthY = subnasaleY + (chinY - subnasaleY) * 0.35;
  const lipHeight = faceHeight * 0.043;
  const lipRatio = target("front-lip-ratio", 0.58);
  const upperShare = lipRatio / (1 + lipRatio);

  return {
    centerX, hairlineY, chinY, glabellaY, subnasaleY, cheekWidth, jawWidth,
    templeWidth, pupilDistance, eyeWidth, innerGap, eyeHeight, eyeY, rise,
    noseWidth, mouthWidth, mouthY, lipHeight, upperShare,
  };
}

function almond(inner: Point, outer: Point, height: number): string {
  const cx = (inner.x + outer.x) / 2;
  const upper = Math.min(inner.y, outer.y) - height * 0.58;
  const lower = Math.max(inner.y, outer.y) + height * 0.47;
  return `M ${inner.x} ${inner.y} Q ${cx} ${upper} ${outer.x} ${outer.y} Q ${cx} ${lower} ${inner.x} ${inner.y} Z`;
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

  const leftInner = { x: g.centerX - g.innerGap / 2, y: g.eyeY + g.rise / 2 };
  const rightInner = { x: g.centerX + g.innerGap / 2, y: g.eyeY + g.rise / 2 };
  const leftOuter = { x: leftInner.x - g.eyeWidth, y: g.eyeY - g.rise / 2 };
  const rightOuter = { x: rightInner.x + g.eyeWidth, y: g.eyeY - g.rise / 2 };
  const leftEye = almond(leftInner, leftOuter, g.eyeHeight);
  const rightEye = almond(rightInner, rightOuter, g.eyeHeight);

  const noseLeft = g.centerX - g.noseWidth / 2;
  const noseRight = g.centerX + g.noseWidth / 2;
  const mouthLeft = g.centerX - g.mouthWidth / 2;
  const mouthRight = g.centerX + g.mouthWidth / 2;
  const browY = g.eyeY - g.eyeWidth * target("front-eyebrow-height", 0.42) - 8;
  const upperLipY = g.mouthY - g.lipHeight * g.upperShare;
  const lowerLipY = g.mouthY + g.lipHeight * (1 - g.upperShare);

  const face = `M ${leftTemple} ${g.hairlineY + 22}
    C ${leftTemple - 26} ${g.hairlineY + 78}, ${leftCheek - 8} ${g.glabellaY + 34}, ${leftCheek} ${g.subnasaleY - 24}
    C ${leftCheek + 2} ${g.subnasaleY + 54}, ${leftJaw - 9} ${g.mouthY + 55}, ${leftJaw} ${g.chinY - 65}
    C ${leftJaw + 27} ${g.chinY - 22}, ${g.centerX - 47} ${g.chinY}, ${g.centerX} ${g.chinY}
    C ${g.centerX + 47} ${g.chinY}, ${rightJaw - 27} ${g.chinY - 22}, ${rightJaw} ${g.chinY - 65}
    C ${rightJaw + 9} ${g.mouthY + 55}, ${rightCheek - 2} ${g.subnasaleY + 54}, ${rightCheek} ${g.subnasaleY - 24}
    C ${rightCheek + 8} ${g.glabellaY + 34}, ${rightTemple + 26} ${g.hairlineY + 78}, ${rightTemple} ${g.hairlineY + 22}
    Q ${g.centerX} ${g.hairlineY - 28} ${leftTemple} ${g.hairlineY + 22} Z`;

  const hair = `M ${leftTemple - 4} ${g.hairlineY + 35}
    C ${leftTemple - 20} ${g.hairlineY - 8}, ${g.centerX - 112} 52, ${g.centerX - 8} 47
    C ${g.centerX + 85} 45, ${rightTemple + 28} ${g.hairlineY - 5}, ${rightTemple + 4} ${g.hairlineY + 41}
    C ${g.centerX + 75} ${g.hairlineY + 3}, ${g.centerX + 20} ${g.hairlineY + 15}, ${g.centerX - 14} ${g.hairlineY + 27}
    C ${g.centerX - 48} ${g.hairlineY + 11}, ${g.centerX - 92} ${g.hairlineY + 13}, ${leftTemple - 4} ${g.hairlineY + 35} Z`;

  const upperLip = `M ${mouthLeft} ${g.mouthY} Q ${g.centerX - 27} ${upperLipY - 2} ${g.centerX} ${upperLipY + 1} Q ${g.centerX + 27} ${upperLipY - 2} ${mouthRight} ${g.mouthY} Q ${g.centerX} ${g.mouthY + 2} ${mouthLeft} ${g.mouthY} Z`;
  const lowerLip = `M ${mouthLeft} ${g.mouthY} Q ${g.centerX} ${lowerLipY + 5} ${mouthRight} ${g.mouthY} Q ${g.centerX} ${g.mouthY + 2} ${mouthLeft} ${g.mouthY} Z`;

  return (
    <svg viewBox="0 0 600 600" role="img" aria-label={`Front target face in ${mode} mode`} className="h-auto w-full">
      <defs>
        <linearGradient id="frontSkin" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ead2c2" />
          <stop offset="60%" stopColor="#d9b09a" />
          <stop offset="100%" stopColor="#c99278" />
        </linearGradient>
        <linearGradient id="frontHair" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#2b2928" />
          <stop offset="100%" stopColor="#49413d" />
        </linearGradient>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={face} fill="url(#frontSkin)" stroke="#6f554a" strokeWidth="1.7" />
          <path d={hair} fill="url(#frontHair)" />
          <ellipse cx={leftCheek - 9} cy={g.eyeY + 85} rx="17" ry="40" fill="#d7a98f" stroke="#7f5d50" strokeWidth="1.2" />
          <ellipse cx={rightCheek + 9} cy={g.eyeY + 85} rx="17" ry="40" fill="#d7a98f" stroke="#7f5d50" strokeWidth="1.2" />

          <path d={`M ${leftTemple + 12} ${g.hairlineY + 50} C ${leftCheek - 3} ${g.eyeY + 78}, ${leftJaw + 10} ${g.mouthY + 68}, ${g.centerX - 74} ${g.chinY - 24}`} fill="none" stroke="#a56f5f" strokeWidth="18" strokeLinecap="round" opacity="0.08" />
          <path d={`M ${rightTemple - 12} ${g.hairlineY + 50} C ${rightCheek + 3} ${g.eyeY + 78}, ${rightJaw - 10} ${g.mouthY + 68}, ${g.centerX + 74} ${g.chinY - 24}`} fill="none" stroke="#fff5ec" strokeWidth="14" strokeLinecap="round" opacity="0.12" />

          <path d={leftEye} fill="#f7f2ed" stroke="#55443d" strokeWidth="1.8" />
          <path d={rightEye} fill="#f7f2ed" stroke="#55443d" strokeWidth="1.8" />
          <ellipse cx={leftPupil} cy={g.eyeY - 1} rx="9" ry="10.5" fill="#6e675f" />
          <ellipse cx={rightPupil} cy={g.eyeY - 1} rx="9" ry="10.5" fill="#6e675f" />
          <circle cx={leftPupil} cy={g.eyeY} r="4.5" fill="#242120" />
          <circle cx={rightPupil} cy={g.eyeY} r="4.5" fill="#242120" />
          <circle cx={leftPupil - 2.5} cy={g.eyeY - 4} r="1.7" fill="#fff" />
          <circle cx={rightPupil - 2.5} cy={g.eyeY - 4} r="1.7" fill="#fff" />

          <path d={`M ${leftOuter.x + 5} ${browY + 7} Q ${leftPupil} ${browY - 8} ${leftInner.x - 4} ${browY + 1}`} fill="none" stroke="#413934" strokeWidth="6.5" strokeLinecap="round" />
          <path d={`M ${rightInner.x + 4} ${browY + 1} Q ${rightPupil} ${browY - 8} ${rightOuter.x - 5} ${browY + 7}`} fill="none" stroke="#413934" strokeWidth="6.5" strokeLinecap="round" />

          <path d={`M ${g.centerX - 5} ${g.glabellaY + 13} C ${g.centerX - 12} ${g.eyeY + 45}, ${g.centerX - 16} ${g.subnasaleY - 30}, ${noseLeft + 9} ${g.subnasaleY - 7}`} fill="none" stroke="#9e6e5c" strokeWidth="1.8" strokeLinecap="round" opacity="0.7" />
          <path d={`M ${g.centerX + 5} ${g.glabellaY + 13} C ${g.centerX + 11} ${g.eyeY + 45}, ${g.centerX + 16} ${g.subnasaleY - 30}, ${noseRight - 9} ${g.subnasaleY - 7}`} fill="none" stroke="#f5e0d2" strokeWidth="1.8" strokeLinecap="round" opacity="0.85" />
          <path d={`M ${noseLeft} ${g.subnasaleY - 2} Q ${g.centerX - 20} ${g.subnasaleY + 7} ${g.centerX} ${g.subnasaleY + 3} Q ${g.centerX + 20} ${g.subnasaleY + 7} ${noseRight} ${g.subnasaleY - 2}`} fill="none" stroke="#815b4e" strokeWidth="1.7" />
          <ellipse cx={g.centerX - 17} cy={g.subnasaleY + 3} rx="4.8" ry="2.4" fill="#60483f" opacity="0.65" />
          <ellipse cx={g.centerX + 17} cy={g.subnasaleY + 3} rx="4.8" ry="2.4" fill="#60483f" opacity="0.65" />

          <path d={upperLip} fill="#9f6265" />
          <path d={lowerLip} fill="#b97878" />
          <path d={`M ${mouthLeft + 4} ${g.mouthY} Q ${g.centerX} ${g.mouthY + 2} ${mouthRight - 4} ${g.mouthY}`} fill="none" stroke="#694147" strokeWidth="1.2" />
          <path d={`M ${g.centerX - 31} ${g.chinY - 27} Q ${g.centerX} ${g.chinY - 17} ${g.centerX + 31} ${g.chinY - 27}`} fill="none" stroke="#a47765" strokeWidth="1.2" opacity="0.5" />
        </g>
      ) : (
        <g>
          <path d={face} fill="none" stroke="var(--ink)" strokeWidth="1.6" />
          <path d={leftEye} fill="none" stroke="var(--ink)" strokeWidth="1.4" />
          <path d={rightEye} fill="none" stroke="var(--ink)" strokeWidth="1.4" />
          <path d={`M ${leftOuter.x + 5} ${browY + 7} Q ${leftPupil} ${browY - 8} ${leftInner.x - 4} ${browY + 1}`} fill="none" stroke="var(--ink)" strokeWidth="2" />
          <path d={`M ${rightInner.x + 4} ${browY + 1} Q ${rightPupil} ${browY - 8} ${rightOuter.x - 5} ${browY + 7}`} fill="none" stroke="var(--ink)" strokeWidth="2" />
          <path d={`M ${g.centerX} ${g.glabellaY + 14} L ${g.centerX} ${g.subnasaleY - 14} M ${noseLeft} ${g.subnasaleY - 2} Q ${g.centerX} ${g.subnasaleY + 7} ${noseRight} ${g.subnasaleY - 2}`} fill="none" stroke="var(--ink)" strokeWidth="1.4" />
          <path d={upperLip} fill="none" stroke="var(--ink)" strokeWidth="1.2" />
          <path d={lowerLip} fill="none" stroke="var(--ink)" strokeWidth="1.2" />
          <g fill="none" stroke="var(--muted)" strokeWidth="1" strokeDasharray="5 5">
            <line x1="105" y1={g.hairlineY} x2="495" y2={g.hairlineY} />
            <line x1="105" y1={g.glabellaY} x2="495" y2={g.glabellaY} />
            <line x1="105" y1={g.subnasaleY} x2="495" y2={g.subnasaleY} />
            <line x1="105" y1={g.chinY} x2="495" y2={g.chinY} />
            <line x1={g.centerX} y1="65" x2={g.centerX} y2="550" />
            <line x1={leftOuter.x} y1={leftOuter.y} x2={leftInner.x} y2={leftInner.y} />
            <line x1={rightInner.x} y1={rightInner.y} x2={rightOuter.x} y2={rightOuter.y} />
            <line x1={noseLeft} y1={g.subnasaleY - 2} x2={noseRight} y2={g.subnasaleY - 2} />
            <line x1={mouthLeft} y1={g.mouthY} x2={mouthRight} y2={g.mouthY} />
          </g>
          {[{x:g.centerX,y:g.hairlineY},{x:g.centerX,y:g.glabellaY},{x:g.centerX,y:g.subnasaleY},{x:g.centerX,y:g.chinY},{x:leftCheek,y:g.subnasaleY-24},{x:rightCheek,y:g.subnasaleY-24},{x:leftJaw,y:g.chinY-65},{x:rightJaw,y:g.chinY-65},{x:leftPupil,y:g.eyeY},{x:rightPupil,y:g.eyeY},{x:noseLeft,y:g.subnasaleY-2},{x:noseRight,y:g.subnasaleY-2},{x:mouthLeft,y:g.mouthY},{x:mouthRight,y:g.mouthY}].map((p,i)=><circle key={i} cx={p.x} cy={p.y} r="3.8" fill="white" stroke="var(--accent)" strokeWidth="1.8" />)}
          <g fill="var(--muted)" fontSize="11">
            <text x="112" y={g.hairlineY - 7}>upper third</text>
            <text x="112" y={g.glabellaY - 7}>middle third</text>
            <text x="112" y={g.subnasaleY - 7}>lower third</text>
            <text x={rightOuter.x + 10} y={rightOuter.y - 7}>positive canthal tilt</text>
          </g>
        </g>
      )}
    </svg>
  );
}

function profileGeometry() {
  const trichion = { x: 292, y: 92 };
  const chinY = 500;
  const profileHeight = chinY - trichion.y;
  const foreheadShift = Math.tan(target("profile-forehead-slope", 16) * Math.PI / 180) * 72;
  const upperForehead = { x: trichion.x + foreheadShift * 0.55, y: 157 };
  const glabella = { x: upperForehead.x + 17, y: 214 };
  const nasion = { x: glabella.x - 7, y: 239 };

  const noseLength = clamp(profileHeight * target("profile-nose-length", 0.3), 116, 126);
  const projection = noseLength * clamp(target("profile-goode", 0.58), 0.54, 0.62);
  const pronasale = { x: nasion.x + projection + 25, y: nasion.y + noseLength * 0.47 };
  const tipRotation = target("profile-tip-rotation", 100);
  const columella = { x: pronasale.x - 26, y: pronasale.y + 22 + (tipRotation - 100) * 0.12 };
  const subnasale = { x: columella.x - 9, y: columella.y + 11 };
  const upperLip = { x: subnasale.x + 9, y: subnasale.y + 31 };
  const stomion = { x: upperLip.x - 3, y: upperLip.y + 14 };
  const lowerLip = { x: upperLip.x + 5, y: stomion.y + 14 };
  const sulcus = { x: lowerLip.x - 17, y: lowerLip.y + 26 };
  const pogonion = { x: upperLip.x + 8, y: chinY - 49 };
  const menton = { x: pogonion.x - 26, y: chinY };

  const plane = clamp(target("profile-mandibular-plane", 23), 18, 28);
  const rad = (180 + plane) * Math.PI / 180;
  const gonion = { x: menton.x + Math.cos(rad) * 142, y: menton.y + Math.sin(rad) * 142 };
  const ramus = { x: gonion.x - 4, y: gonion.y - 122 };
  const tragion = { x: ramus.x + 7, y: 281 };
  const orbitale = { x: nasion.x + 10, y: 272 };
  const cheek = { x: orbitale.x + 24, y: orbitale.y + 50 };
  const neckFront = { x: menton.x - 8, y: 560 };
  const neckBack = { x: gonion.x - 58, y: 560 };
  const skullBack = { x: 194, y: 205 };
  const crown = { x: 236, y: 62 };

  return { trichion, upperForehead, glabella, nasion, pronasale, columella, subnasale, upperLip, stomion, lowerLip, sulcus, pogonion, menton, gonion, ramus, tragion, orbitale, cheek, neckFront, neckBack, skullBack, crown };
}

function ProfileFace({ mode }: { mode: RenderMode }) {
  const g = useMemo(profileGeometry, []);
  const faceContour = `M ${g.trichion.x} ${g.trichion.y}
    C ${g.upperForehead.x - 10} ${g.upperForehead.y - 35}, ${g.upperForehead.x + 1} ${g.upperForehead.y - 8}, ${g.upperForehead.x} ${g.upperForehead.y}
    C ${g.upperForehead.x + 5} ${g.upperForehead.y + 31}, ${g.glabella.x + 5} ${g.glabella.y - 14}, ${g.glabella.x} ${g.glabella.y}
    Q ${g.nasion.x - 8} ${g.nasion.y - 7} ${g.nasion.x} ${g.nasion.y}
    C ${g.nasion.x + 28} ${g.nasion.y + 4}, ${g.pronasale.x - 25} ${g.pronasale.y - 13}, ${g.pronasale.x} ${g.pronasale.y}
    Q ${g.columella.x + 13} ${g.columella.y - 7} ${g.columella.x} ${g.columella.y}
    Q ${g.subnasale.x + 8} ${g.subnasale.y - 3} ${g.subnasale.x} ${g.subnasale.y}
    Q ${g.upperLip.x + 12} ${g.upperLip.y - 7} ${g.upperLip.x} ${g.upperLip.y}
    Q ${g.stomion.x + 6} ${g.stomion.y - 1} ${g.stomion.x} ${g.stomion.y}
    Q ${g.lowerLip.x + 12} ${g.lowerLip.y - 2} ${g.lowerLip.x} ${g.lowerLip.y}
    Q ${g.sulcus.x - 6} ${g.sulcus.y - 2} ${g.sulcus.x} ${g.sulcus.y}
    Q ${g.pogonion.x + 17} ${g.pogonion.y - 16} ${g.pogonion.x} ${g.pogonion.y}
    Q ${g.menton.x + 21} ${g.menton.y + 1} ${g.menton.x} ${g.menton.y}
    C ${g.menton.x - 2} ${g.menton.y + 22}, ${g.neckFront.x} ${g.neckFront.y - 18}, ${g.neckFront.x} ${g.neckFront.y}`;

  const backContour = `M ${g.trichion.x} ${g.trichion.y}
    C ${g.crown.x + 57} ${g.crown.y - 16}, ${g.skullBack.x + 3} ${g.skullBack.y - 95}, ${g.skullBack.x} ${g.skullBack.y}
    C ${g.skullBack.x - 11} ${g.skullBack.y + 73}, ${g.ramus.x - 29} ${g.ramus.y - 28}, ${g.ramus.x} ${g.ramus.y}
    L ${g.gonion.x} ${g.gonion.y}
    C ${g.gonion.x - 17} ${g.gonion.y + 50}, ${g.neckBack.x} ${g.neckBack.y - 19}, ${g.neckBack.x} ${g.neckBack.y}`;

  const headFill = `${faceContour} L ${g.neckBack.x} ${g.neckBack.y} C ${g.gonion.x - 17} ${g.gonion.y + 50}, ${g.gonion.x} ${g.gonion.y + 16}, ${g.gonion.x} ${g.gonion.y} L ${g.ramus.x} ${g.ramus.y} C ${g.ramus.x - 29} ${g.ramus.y - 28}, ${g.skullBack.x - 11} ${g.skullBack.y + 73}, ${g.skullBack.x} ${g.skullBack.y} C ${g.skullBack.x + 3} ${g.skullBack.y - 95}, ${g.crown.x + 57} ${g.crown.y - 16}, ${g.trichion.x} ${g.trichion.y} Z`;

  const hair = `M ${g.trichion.x} ${g.trichion.y} C ${g.crown.x + 51} ${g.crown.y - 20}, ${g.skullBack.x - 3} ${g.skullBack.y - 92}, ${g.skullBack.x} ${g.skullBack.y} C ${g.skullBack.x + 15} ${g.skullBack.y - 10}, ${g.ramus.x - 10} ${g.ramus.y - 94}, ${g.ramus.x + 10} ${g.ramus.y - 72} C ${g.ramus.x + 25} ${g.ramus.y - 103}, ${g.trichion.x - 18} ${g.trichion.y + 17}, ${g.trichion.x} ${g.trichion.y} Z`;

  return (
    <svg viewBox="0 0 600 600" role="img" aria-label={`Profile target face in ${mode} mode`} className="h-auto w-full">
      <defs>
        <linearGradient id="profileSkin" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ead0bf" />
          <stop offset="58%" stopColor="#d9ad94" />
          <stop offset="100%" stopColor="#c98f75" />
        </linearGradient>
        <linearGradient id="profileHair" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#292726" />
          <stop offset="100%" stopColor="#493e39" />
        </linearGradient>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={headFill} fill="url(#profileSkin)" stroke="#6f554a" strokeWidth="1.7" strokeLinejoin="round" />
          <path d={hair} fill="url(#profileHair)" />
          <ellipse cx={g.tragion.x} cy={g.tragion.y + 31} rx="25" ry="39" fill="#d5a187" stroke="#805d50" strokeWidth="1.2" />
          <path d={`M ${g.tragion.x - 3} ${g.tragion.y + 11} C ${g.tragion.x + 14} ${g.tragion.y + 21}, ${g.tragion.x + 13} ${g.tragion.y + 48}, ${g.tragion.x - 3} ${g.tragion.y + 60} C ${g.tragion.x + 4} ${g.tragion.y + 43}, ${g.tragion.x - 9} ${g.tragion.y + 30}, ${g.tragion.x - 3} ${g.tragion.y + 11}`} fill="none" stroke="#996b5b" strokeWidth="1.2" />

          <path d={`M ${g.orbitale.x - 20} ${g.orbitale.y - 3} Q ${g.orbitale.x + 2} ${g.orbitale.y - 12} ${g.orbitale.x + 20} ${g.orbitale.y - 3} Q ${g.orbitale.x + 3} ${g.orbitale.y + 4} ${g.orbitale.x - 20} ${g.orbitale.y - 3} Z`} fill="#f7f2ed" stroke="#55443d" strokeWidth="1.6" />
          <ellipse cx={g.orbitale.x + 2} cy={g.orbitale.y - 2} rx="7" ry="8" fill="#6e675f" />
          <circle cx={g.orbitale.x + 3} cy={g.orbitale.y - 1} r="3.7" fill="#242120" />
          <path d={`M ${g.orbitale.x - 22} ${g.orbitale.y - 24} Q ${g.orbitale.x + 1} ${g.orbitale.y - 35} ${g.orbitale.x + 27} ${g.orbitale.y - 21}`} fill="none" stroke="#413934" strokeWidth="6" strokeLinecap="round" />

          <path d={`M ${g.nasion.x + 2} ${g.nasion.y + 3} C ${g.nasion.x + 30} ${g.nasion.y + 8}, ${g.pronasale.x - 23} ${g.pronasale.y - 11}, ${g.pronasale.x - 2} ${g.pronasale.y}`} fill="none" stroke="#f4dfd1" strokeWidth="2" opacity="0.8" />
          <ellipse cx={g.columella.x + 4} cy={g.columella.y + 1} rx="7" ry="3.5" fill="#60483f" opacity="0.6" />
          <path d={`M ${g.subnasale.x + 1} ${g.subnasale.y + 3} Q ${g.upperLip.x + 8} ${g.upperLip.y - 7} ${g.upperLip.x} ${g.upperLip.y}`} fill="none" stroke="#955b5f" strokeWidth="4" strokeLinecap="round" />
          <path d={`M ${g.stomion.x} ${g.stomion.y} Q ${g.lowerLip.x + 8} ${g.lowerLip.y - 4} ${g.lowerLip.x} ${g.lowerLip.y}`} fill="none" stroke="#ae6b6d" strokeWidth="4.7" strokeLinecap="round" />
          <path d={`M ${g.upperLip.x - 2} ${g.stomion.y} Q ${g.lowerLip.x} ${g.stomion.y + 1} ${g.lowerLip.x + 1} ${g.stomion.y + 1}`} fill="none" stroke="#674048" strokeWidth="1.2" />
          <path d={`M ${g.sulcus.x - 3} ${g.sulcus.y + 2} Q ${g.pogonion.x - 9} ${g.pogonion.y - 28} ${g.pogonion.x - 1} ${g.pogonion.y - 15}`} fill="none" stroke="#9e705f" strokeWidth="1.3" opacity="0.55" />
        </g>
      ) : (
        <g>
          <path d={faceContour} fill="none" stroke="var(--ink)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          <path d={backContour} fill="none" stroke="var(--ink)" strokeWidth="1.4" strokeLinecap="round" />
          <path d={`M ${g.orbitale.x - 20} ${g.orbitale.y - 3} Q ${g.orbitale.x + 2} ${g.orbitale.y - 12} ${g.orbitale.x + 20} ${g.orbitale.y - 3}`} fill="none" stroke="var(--ink)" strokeWidth="1.4" />
          <ellipse cx={g.tragion.x} cy={g.tragion.y + 31} rx="25" ry="39" fill="none" stroke="var(--ink)" strokeWidth="1.2" />
          <g fill="none" stroke="var(--muted)" strokeWidth="1" strokeDasharray="5 5">
            <line x1={g.tragion.x - 25} y1={g.tragion.y} x2={g.orbitale.x + 165} y2={g.orbitale.y} />
            <line x1={g.nasion.x} y1={g.nasion.y} x2={g.pronasale.x} y2={g.pronasale.y} />
            <line x1={g.pronasale.x} y1={g.pronasale.y} x2={g.pogonion.x} y2={g.pogonion.y} />
            <line x1={g.gonion.x} y1={g.gonion.y} x2={g.menton.x} y2={g.menton.y} />
            <line x1={g.gonion.x} y1={g.gonion.y} x2={g.ramus.x} y2={g.ramus.y} />
          </g>
          {[g.trichion,g.glabella,g.nasion,g.pronasale,g.subnasale,g.upperLip,g.lowerLip,g.pogonion,g.menton,g.gonion,g.tragion,g.orbitale].map((p,i)=><circle key={i} cx={p.x} cy={p.y} r="3.8" fill="white" stroke="var(--accent)" strokeWidth="1.8" />)}
          <g fill="var(--muted)" fontSize="11">
            <text x={g.tragion.x - 5} y={g.tragion.y - 11}>Frankfort plane</text>
            <text x={g.pronasale.x + 9} y={g.pronasale.y - 5}>tip</text>
            <text x={g.pogonion.x + 9} y={g.pogonion.y}>pogonion</text>
            <text x={g.gonion.x - 54} y={g.gonion.y - 9}>gonion</text>
          </g>
        </g>
      )}
    </svg>
  );
}

function Toggle<T extends string>({ value, options, onChange, name }: { value: T; options: readonly T[]; onChange: (value: T) => void; name: string }) {
  return (
    <div className="flex border border-[var(--line)] bg-white p-1" role="group" aria-label={name}>
      {options.map((option) => (
        <button key={option} type="button" onClick={() => onChange(option)} aria-pressed={value === option} className={`px-3 py-2 text-sm capitalize ${value === option ? "bg-[var(--ink)] text-white" : "text-[var(--muted)]"}`}>
          {option === "rendered" ? "Realistic" : option === "profile" ? "Side" : option}
        </button>
      ))}
    </div>
  );
}

export function IdealReferenceFace() {
  const [view, setView] = useState<FaceView>("front");
  const [mode, setMode] = useState<RenderMode>("structure");
  const metrics = view === "front" ? FRONT_TARGETS : PROFILE_TARGETS;

  return (
    <section id="ideal-reference" className="mt-12 border border-[var(--line)] bg-white">
      <div className="border-b border-[var(--line)] p-5 sm:p-7">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--accent)]">Current harmony target</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">The face implied by Mog’s measurements</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--muted)]">Structure shows the scored landmarks and guides. Realistic mode uses the same coordinates with only smooth contour interpolation and restrained editorial shading. Styling never enters the score.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Toggle value={view} options={["front", "profile"] as const} onChange={setView} name="Face view" />
            <Toggle value={mode} options={["structure", "rendered"] as const} onChange={setMode} name="Rendering mode" />
          </div>
        </div>
      </div>
      <div className="grid lg:grid-cols-[minmax(0,1.35fr)_minmax(250px,0.65fr)]">
        <div className="min-h-[520px] border-b border-[var(--line)] bg-[var(--paper)] p-4 sm:p-8 lg:border-b-0 lg:border-r">
          <div className="mx-auto max-w-[560px]">{view === "front" ? <FrontFace mode={mode} /> : <ProfileFace mode={mode} />}</div>
        </div>
        <div className="p-5 sm:p-7">
          <h3 className="font-semibold">Target centers used in this view</h3>
          <p className="mt-2 text-xs leading-5 text-[var(--muted)]">Every numeric target comes directly from the neutral harmony reference bands.</p>
          <dl className="mt-5 divide-y divide-[var(--line)] border-y border-[var(--line)]">
            {metrics.map((metric) => <div key={metric.id} className="flex items-baseline justify-between gap-4 py-2.5 text-sm"><dt className="text-[var(--muted)]">{metric.label}</dt><dd className="font-mono text-xs font-semibold tabular-nums">{label(metric)}</dd></div>)}
          </dl>
          <p className="mt-5 text-xs leading-5 text-[var(--muted)]">The measurements do not uniquely specify skin, hair, or every soft-tissue curve. Those elements are illustrative only; the scored structure remains unchanged between modes.</p>
        </div>
      </div>
    </section>
  );
}
