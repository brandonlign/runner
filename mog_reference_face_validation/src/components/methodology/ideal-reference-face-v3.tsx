"use client";

import { useMemo, useState } from "react";
import { getReferenceBand } from "@/lib/analysis/reference-bands.ts";

type View = "front" | "profile";
type Mode = "structure" | "rendered";
type Point = { x: number; y: number };
type Metric = { id: string; label: string; unit: "ratio" | "degrees" | "distance" };

const FRONT_METRICS: Metric[] = [
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

const PROFILE_METRICS: Metric[] = [
  { id: "profile-forehead-slope", label: "Forehead slope", unit: "degrees" },
  { id: "profile-nasofrontal", label: "Nasofrontal angle", unit: "degrees" },
  { id: "profile-dorsum-angle", label: "Nasal dorsum", unit: "degrees" },
  { id: "profile-tip-rotation", label: "Tip rotation", unit: "degrees" },
  { id: "profile-nasolabial", label: "Nasolabial angle", unit: "degrees" },
  { id: "profile-goode", label: "Goode projection", unit: "ratio" },
  { id: "profile-nose-length", label: "Nose / profile height", unit: "ratio" },
  { id: "profile-total-convexity", label: "Total convexity", unit: "degrees" },
  { id: "profile-upper-e-line", label: "Upper lip to E-line", unit: "distance" },
  { id: "profile-lower-e-line", label: "Lower lip to E-line", unit: "distance" },
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

function display(metric: Metric): string {
  const value = target(metric.id, 0);
  if (metric.unit === "degrees") return `${Math.round(value)}°`;
  if (metric.unit === "distance") return value.toFixed(3);
  return value.toFixed(2);
}

function clamp(value: number, low: number, high: number): number {
  return Math.max(low, Math.min(high, value));
}

function frontGeometry() {
  const cx = 300;
  const hairlineY = 105;
  const chinY = 520;
  const height = chinY - hairlineY;
  const cheekWidth = clamp(height * target("front-bizygomatic-height", 0.78), 320, 338);
  const jawWidth = clamp(cheekWidth / target("front-bizygomatic-bigonial", 1.25), 252, 276);
  const templeWidth = clamp(cheekWidth * target("front-bitemporal-bizygomatic", 0.84), 272, 292);

  const upper = target("front-upper-third", 0.333);
  const middle = target("front-middle-third", 0.333);
  const lower = target("front-lower-third", 0.34);
  const total = upper + middle + lower;
  const glabellaY = hairlineY + height * upper / total;
  const subnasaleY = glabellaY + height * middle / total;

  const pupilDistance = cheekWidth * target("front-interpupil-face", 0.47);
  const spacing = target("front-intercanthal-eye", 1);
  const eyeWidth = pupilDistance / (1 + spacing);
  const innerGap = eyeWidth * spacing;
  const eyeHeight = eyeWidth * target("front-eye-aspect", 0.32);
  const eyeY = glabellaY + (subnasaleY - glabellaY) * 0.25;
  const rise = Math.tan(target("front-average-canthal", 5) * Math.PI / 180) * eyeWidth;

  const noseFromEyes = innerGap * target("front-nose-intercanthal", 1);
  const mouthFromPupils = pupilDistance * target("front-mouth-interpupil", 0.94);
  const mouthFromNose = noseFromEyes / target("front-nose-mouth", 0.66);
  const mouthWidth = mouthFromPupils * 0.72 + mouthFromNose * 0.28;
  const noseWidth = noseFromEyes * 0.74 + mouthWidth * target("front-nose-mouth", 0.66) * 0.26;
  const mouthY = subnasaleY + (chinY - subnasaleY) * 0.37;
  const lipHeight = height * 0.045;
  const lipRatio = target("front-lip-ratio", 0.58);
  const upperShare = lipRatio / (1 + lipRatio);

  return { cx, hairlineY, chinY, height, cheekWidth, jawWidth, templeWidth, glabellaY, subnasaleY, pupilDistance, eyeWidth, innerGap, eyeHeight, eyeY, rise, noseWidth, mouthWidth, mouthY, lipHeight, upperShare };
}

function eyePath(inner: Point, outer: Point, height: number): string {
  const centerX = (inner.x + outer.x) / 2;
  const top = Math.min(inner.y, outer.y) - height * 0.62;
  const bottom = Math.max(inner.y, outer.y) + height * 0.44;
  return `M ${inner.x} ${inner.y} Q ${centerX} ${top} ${outer.x} ${outer.y} Q ${centerX} ${bottom} ${inner.x} ${inner.y} Z`;
}

function FrontPortrait({ mode }: { mode: Mode }) {
  const g = useMemo(frontGeometry, []);
  const leftCheek = g.cx - g.cheekWidth / 2;
  const rightCheek = g.cx + g.cheekWidth / 2;
  const leftJaw = g.cx - g.jawWidth / 2;
  const rightJaw = g.cx + g.jawWidth / 2;
  const leftTemple = g.cx - g.templeWidth / 2;
  const rightTemple = g.cx + g.templeWidth / 2;
  const leftPupil = g.cx - g.pupilDistance / 2;
  const rightPupil = g.cx + g.pupilDistance / 2;

  const leftInner = { x: g.cx - g.innerGap / 2, y: g.eyeY + g.rise / 2 };
  const rightInner = { x: g.cx + g.innerGap / 2, y: g.eyeY + g.rise / 2 };
  const leftOuter = { x: leftInner.x - g.eyeWidth, y: g.eyeY - g.rise / 2 };
  const rightOuter = { x: rightInner.x + g.eyeWidth, y: g.eyeY - g.rise / 2 };
  const leftEye = eyePath(leftInner, leftOuter, g.eyeHeight);
  const rightEye = eyePath(rightInner, rightOuter, g.eyeHeight);

  const noseLeft = g.cx - g.noseWidth / 2;
  const noseRight = g.cx + g.noseWidth / 2;
  const mouthLeft = g.cx - g.mouthWidth / 2;
  const mouthRight = g.cx + g.mouthWidth / 2;
  const browY = g.eyeY - g.eyeWidth * target("front-eyebrow-height", 0.42) - 6;
  const upperLipY = g.mouthY - g.lipHeight * g.upperShare;
  const lowerLipY = g.mouthY + g.lipHeight * (1 - g.upperShare);

  const face = `M ${leftTemple} ${g.hairlineY + 24}
    C ${leftTemple - 21} ${g.hairlineY + 75}, ${leftCheek - 8} ${g.glabellaY + 30}, ${leftCheek} ${g.subnasaleY - 27}
    C ${leftCheek + 2} ${g.subnasaleY + 47}, ${leftJaw - 8} ${g.mouthY + 52}, ${leftJaw} ${g.chinY - 68}
    C ${leftJaw + 26} ${g.chinY - 29}, ${g.cx - 51} ${g.chinY - 2}, ${g.cx} ${g.chinY}
    C ${g.cx + 51} ${g.chinY - 2}, ${rightJaw - 26} ${g.chinY - 29}, ${rightJaw} ${g.chinY - 68}
    C ${rightJaw + 8} ${g.mouthY + 52}, ${rightCheek - 2} ${g.subnasaleY + 47}, ${rightCheek} ${g.subnasaleY - 27}
    C ${rightCheek + 8} ${g.glabellaY + 30}, ${rightTemple + 21} ${g.hairlineY + 75}, ${rightTemple} ${g.hairlineY + 24}
    Q ${g.cx} ${g.hairlineY - 24} ${leftTemple} ${g.hairlineY + 24} Z`;

  const hair = `M ${leftTemple - 3} ${g.hairlineY + 34}
    C ${leftTemple - 17} ${g.hairlineY - 6}, ${g.cx - 101} 53, ${g.cx - 2} 49
    C ${g.cx + 91} 48, ${rightTemple + 21} ${g.hairlineY - 3}, ${rightTemple + 3} ${g.hairlineY + 36}
    C ${g.cx + 68} ${g.hairlineY + 1}, ${g.cx + 25} ${g.hairlineY + 12}, ${g.cx - 11} ${g.hairlineY + 25}
    C ${g.cx - 45} ${g.hairlineY + 11}, ${g.cx - 86} ${g.hairlineY + 13}, ${leftTemple - 3} ${g.hairlineY + 34} Z`;

  const neck = `M ${g.cx - 65} ${g.chinY - 8} C ${g.cx - 58} ${g.chinY + 18}, ${g.cx - 66} 556, ${g.cx - 96} 575 L ${g.cx + 96} 575 C ${g.cx + 66} 556, ${g.cx + 58} ${g.chinY + 18}, ${g.cx + 65} ${g.chinY - 8} Z`;
  const shoulders = `M 116 600 C 154 566, ${g.cx - 108} 561, ${g.cx - 80} 552 C ${g.cx - 41} 575, ${g.cx + 41} 575, ${g.cx + 80} 552 C ${g.cx + 108} 561, 446 566, 484 600 Z`;

  const upperLip = `M ${mouthLeft} ${g.mouthY} Q ${g.cx - 29} ${upperLipY - 3} ${g.cx} ${upperLipY + 1} Q ${g.cx + 29} ${upperLipY - 3} ${mouthRight} ${g.mouthY} Q ${g.cx} ${g.mouthY + 2} ${mouthLeft} ${g.mouthY} Z`;
  const lowerLip = `M ${mouthLeft} ${g.mouthY} Q ${g.cx} ${lowerLipY + 5} ${mouthRight} ${g.mouthY} Q ${g.cx} ${g.mouthY + 2} ${mouthLeft} ${g.mouthY} Z`;

  const landmarks = [
    { x: g.cx, y: g.hairlineY }, { x: g.cx, y: g.glabellaY }, { x: g.cx, y: g.subnasaleY }, { x: g.cx, y: g.chinY },
    { x: leftCheek, y: g.subnasaleY - 27 }, { x: rightCheek, y: g.subnasaleY - 27 }, { x: leftJaw, y: g.chinY - 68 }, { x: rightJaw, y: g.chinY - 68 },
    { x: leftPupil, y: g.eyeY }, { x: rightPupil, y: g.eyeY }, { x: noseLeft, y: g.subnasaleY - 2 }, { x: noseRight, y: g.subnasaleY - 2 }, { x: mouthLeft, y: g.mouthY }, { x: mouthRight, y: g.mouthY },
  ];

  return (
    <svg viewBox="0 0 600 620" role="img" aria-label={`Front target face in ${mode} mode`} className="h-auto w-full">
      <defs>
        <linearGradient id="v3FrontSkin" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#eed9ca" />
          <stop offset="55%" stopColor="#dcb49d" />
          <stop offset="100%" stopColor="#c99177" />
        </linearGradient>
        <linearGradient id="v3FrontHair" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#282727" />
          <stop offset="100%" stopColor="#48413d" />
        </linearGradient>
        <radialGradient id="v3FrontLight" cx="48%" cy="35%" r="72%">
          <stop offset="0%" stopColor="#fff7f0" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#6e3428" stopOpacity="0" />
        </radialGradient>
        <filter id="v3Soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="7" /></filter>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={shoulders} fill="#c4b5aa" />
          <path d={neck} fill="url(#v3FrontSkin)" />
          <path d={face} fill="url(#v3FrontSkin)" stroke="#75584c" strokeWidth="1.35" />
          <path d={hair} fill="url(#v3FrontHair)" />
          <ellipse cx={leftCheek - 9} cy={g.eyeY + 84} rx="16" ry="39" fill="#d5a086" stroke="#835d4e" strokeWidth="1" />
          <ellipse cx={rightCheek + 9} cy={g.eyeY + 84} rx="16" ry="39" fill="#d5a086" stroke="#835d4e" strokeWidth="1" />
          <ellipse cx={g.cx} cy={g.eyeY + 77} rx={g.cheekWidth * 0.47} ry="190" fill="url(#v3FrontLight)" />
          <ellipse cx={leftPupil - 18} cy={g.eyeY + 72} rx="52" ry="30" fill="#9a5548" opacity="0.08" filter="url(#v3Soft)" />
          <ellipse cx={rightPupil + 18} cy={g.eyeY + 72} rx="52" ry="30" fill="#9a5548" opacity="0.08" filter="url(#v3Soft)" />

          <path d={leftEye} fill="#fbf7f3" stroke="#55443d" strokeWidth="1.5" />
          <path d={rightEye} fill="#fbf7f3" stroke="#55443d" strokeWidth="1.5" />
          <ellipse cx={leftPupil} cy={g.eyeY - 1} rx="9.5" ry="11" fill="#77746c" />
          <ellipse cx={rightPupil} cy={g.eyeY - 1} rx="9.5" ry="11" fill="#77746c" />
          <circle cx={leftPupil} cy={g.eyeY} r="4.5" fill="#252321" />
          <circle cx={rightPupil} cy={g.eyeY} r="4.5" fill="#252321" />
          <circle cx={leftPupil - 2.7} cy={g.eyeY - 4} r="1.7" fill="#fff" />
          <circle cx={rightPupil - 2.7} cy={g.eyeY - 4} r="1.7" fill="#fff" />
          <path d={`M ${leftOuter.x + 4} ${browY + 7} Q ${leftPupil} ${browY - 8} ${leftInner.x - 4} ${browY + 1}`} fill="none" stroke="#443a35" strokeWidth="6" strokeLinecap="round" />
          <path d={`M ${rightInner.x + 4} ${browY + 1} Q ${rightPupil} ${browY - 8} ${rightOuter.x - 4} ${browY + 7}`} fill="none" stroke="#443a35" strokeWidth="6" strokeLinecap="round" />

          <path d={`M ${g.cx - 6} ${g.glabellaY + 16} C ${g.cx - 13} ${g.eyeY + 38}, ${g.cx - 15} ${g.subnasaleY - 30}, ${noseLeft + 9} ${g.subnasaleY - 8}`} fill="none" stroke="#9e6e5c" strokeWidth="1.6" strokeLinecap="round" opacity="0.68" />
          <path d={`M ${g.cx + 5} ${g.glabellaY + 16} C ${g.cx + 10} ${g.eyeY + 37}, ${g.cx + 15} ${g.subnasaleY - 30}, ${noseRight - 8} ${g.subnasaleY - 8}`} fill="none" stroke="#f7e7dc" strokeWidth="1.7" strokeLinecap="round" opacity="0.8" />
          <path d={`M ${noseLeft} ${g.subnasaleY - 2} Q ${g.cx - 20} ${g.subnasaleY + 7} ${g.cx} ${g.subnasaleY + 3} Q ${g.cx + 20} ${g.subnasaleY + 7} ${noseRight} ${g.subnasaleY - 2}`} fill="none" stroke="#80594c" strokeWidth="1.5" />
          <ellipse cx={g.cx - 17} cy={g.subnasaleY + 3} rx="4.6" ry="2.2" fill="#60473e" opacity="0.58" />
          <ellipse cx={g.cx + 17} cy={g.subnasaleY + 3} rx="4.6" ry="2.2" fill="#60473e" opacity="0.58" />

          <path d={upperLip} fill="#9e6266" opacity="0.92" />
          <path d={lowerLip} fill="#b77a79" opacity="0.92" />
          <path d={`M ${mouthLeft + 4} ${g.mouthY} Q ${g.cx} ${g.mouthY + 2} ${mouthRight - 4} ${g.mouthY}`} fill="none" stroke="#664047" strokeWidth="1.1" />
          <path d={`M ${g.cx - 30} ${g.chinY - 27} Q ${g.cx} ${g.chinY - 18} ${g.cx + 30} ${g.chinY - 27}`} fill="none" stroke="#a27664" strokeWidth="1.1" opacity="0.44" />
        </g>
      ) : (
        <g>
          <path d={face} fill="none" stroke="var(--ink)" strokeWidth="1.55" />
          <path d={leftEye} fill="none" stroke="var(--ink)" strokeWidth="1.35" />
          <path d={rightEye} fill="none" stroke="var(--ink)" strokeWidth="1.35" />
          <path d={`M ${leftOuter.x + 4} ${browY + 7} Q ${leftPupil} ${browY - 8} ${leftInner.x - 4} ${browY + 1}`} fill="none" stroke="var(--ink)" strokeWidth="1.9" />
          <path d={`M ${rightInner.x + 4} ${browY + 1} Q ${rightPupil} ${browY - 8} ${rightOuter.x - 4} ${browY + 7}`} fill="none" stroke="var(--ink)" strokeWidth="1.9" />
          <path d={`M ${g.cx} ${g.glabellaY + 14} L ${g.cx} ${g.subnasaleY - 14} M ${noseLeft} ${g.subnasaleY - 2} Q ${g.cx} ${g.subnasaleY + 7} ${noseRight} ${g.subnasaleY - 2}`} fill="none" stroke="var(--ink)" strokeWidth="1.35" />
          <path d={upperLip} fill="none" stroke="var(--ink)" strokeWidth="1.15" />
          <path d={lowerLip} fill="none" stroke="var(--ink)" strokeWidth="1.15" />
          <g fill="none" stroke="var(--muted)" strokeWidth="1" strokeDasharray="5 5">
            <line x1="105" y1={g.hairlineY} x2="495" y2={g.hairlineY} />
            <line x1="105" y1={g.glabellaY} x2="495" y2={g.glabellaY} />
            <line x1="105" y1={g.subnasaleY} x2="495" y2={g.subnasaleY} />
            <line x1="105" y1={g.chinY} x2="495" y2={g.chinY} />
            <line x1={g.cx} y1="65" x2={g.cx} y2="548" />
            <line x1={leftOuter.x} y1={leftOuter.y} x2={leftInner.x} y2={leftInner.y} />
            <line x1={rightInner.x} y1={rightInner.y} x2={rightOuter.x} y2={rightOuter.y} />
            <line x1={noseLeft} y1={g.subnasaleY - 2} x2={noseRight} y2={g.subnasaleY - 2} />
            <line x1={mouthLeft} y1={g.mouthY} x2={mouthRight} y2={g.mouthY} />
          </g>
          {landmarks.map((p, index) => <circle key={index} cx={p.x} cy={p.y} r="3.7" fill="white" stroke="var(--accent)" strokeWidth="1.7" />)}
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
  const trichion = { x: 302, y: 100 };
  const chinY = 502;
  const profileHeight = chinY - trichion.y;
  const foreheadSlope = target("profile-forehead-slope", 16);
  const upperForehead = { x: trichion.x + Math.tan(foreheadSlope * Math.PI / 180) * 37, y: 160 };
  const glabella = { x: upperForehead.x + 17, y: 214 };
  const nasion = { x: glabella.x - 7, y: 239 };
  const noseLength = clamp(profileHeight * target("profile-nose-length", 0.3), 116, 126);
  const projection = noseLength * clamp(target("profile-goode", 0.58), 0.54, 0.62);
  const pronasale = { x: nasion.x + projection + 22, y: nasion.y + noseLength * 0.47 };
  const tipRotation = target("profile-tip-rotation", 100);
  const columella = { x: pronasale.x - 25, y: pronasale.y + 21 + (tipRotation - 100) * 0.12 };
  const subnasale = { x: columella.x - 9, y: columella.y + 11 };
  const upperLip = { x: subnasale.x + 9, y: subnasale.y + 31 };
  const stomion = { x: upperLip.x - 3, y: upperLip.y + 14 };
  const lowerLip = { x: upperLip.x + 5, y: stomion.y + 14 };
  const sulcus = { x: lowerLip.x - 17, y: lowerLip.y + 26 };
  const pogonion = { x: upperLip.x + 8, y: chinY - 49 };
  const menton = { x: pogonion.x - 26, y: chinY };
  const plane = clamp(target("profile-mandibular-plane", 23), 18, 28);
  const radians = (180 + plane) * Math.PI / 180;
  const gonion = { x: menton.x + Math.cos(radians) * 140, y: menton.y + Math.sin(radians) * 140 };
  const ramus = { x: gonion.x - 2, y: gonion.y - 117 };
  const tragion = { x: ramus.x + 8, y: 283 };
  const orbitale = { x: nasion.x + 9, y: 271 };
  const cheek = { x: orbitale.x + 22, y: orbitale.y + 48 };
  const neckFront = { x: menton.x - 8, y: 548 };
  const neckBack = { x: gonion.x - 45, y: 548 };
  const skullBack = { x: 188, y: 210 };
  const crown = { x: 231, y: 73 };
  return { trichion, upperForehead, glabella, nasion, pronasale, columella, subnasale, upperLip, stomion, lowerLip, sulcus, pogonion, menton, gonion, ramus, tragion, orbitale, cheek, neckFront, neckBack, skullBack, crown };
}

function ProfilePortrait({ mode }: { mode: Mode }) {
  const g = useMemo(profileGeometry, []);
  const faceContour = `M ${g.trichion.x} ${g.trichion.y}
    C ${g.upperForehead.x - 9} ${g.upperForehead.y - 35}, ${g.upperForehead.x + 1} ${g.upperForehead.y - 8}, ${g.upperForehead.x} ${g.upperForehead.y}
    C ${g.upperForehead.x + 5} ${g.upperForehead.y + 30}, ${g.glabella.x + 5} ${g.glabella.y - 14}, ${g.glabella.x} ${g.glabella.y}
    Q ${g.nasion.x - 8} ${g.nasion.y - 7} ${g.nasion.x} ${g.nasion.y}
    C ${g.nasion.x + 28} ${g.nasion.y + 5}, ${g.pronasale.x - 24} ${g.pronasale.y - 13}, ${g.pronasale.x} ${g.pronasale.y}
    Q ${g.columella.x + 13} ${g.columella.y - 7} ${g.columella.x} ${g.columella.y}
    Q ${g.subnasale.x + 8} ${g.subnasale.y - 3} ${g.subnasale.x} ${g.subnasale.y}
    Q ${g.upperLip.x + 12} ${g.upperLip.y - 7} ${g.upperLip.x} ${g.upperLip.y}
    Q ${g.stomion.x + 6} ${g.stomion.y - 1} ${g.stomion.x} ${g.stomion.y}
    Q ${g.lowerLip.x + 12} ${g.lowerLip.y - 2} ${g.lowerLip.x} ${g.lowerLip.y}
    Q ${g.sulcus.x - 6} ${g.sulcus.y - 2} ${g.sulcus.x} ${g.sulcus.y}
    Q ${g.pogonion.x + 17} ${g.pogonion.y - 16} ${g.pogonion.x} ${g.pogonion.y}
    Q ${g.menton.x + 21} ${g.menton.y + 1} ${g.menton.x} ${g.menton.y}
    C ${g.menton.x - 2} ${g.menton.y + 21}, ${g.neckFront.x} ${g.neckFront.y - 15}, ${g.neckFront.x} ${g.neckFront.y}`;

  const backContour = `M ${g.trichion.x} ${g.trichion.y}
    C ${g.crown.x + 61} ${g.crown.y - 17}, ${g.skullBack.x + 4} ${g.skullBack.y - 96}, ${g.skullBack.x} ${g.skullBack.y}
    C ${g.skullBack.x - 10} ${g.skullBack.y + 67}, ${g.ramus.x - 27} ${g.ramus.y - 24}, ${g.ramus.x} ${g.ramus.y}
    L ${g.gonion.x} ${g.gonion.y}
    C ${g.gonion.x - 12} ${g.gonion.y + 45}, ${g.neckBack.x} ${g.neckBack.y - 16}, ${g.neckBack.x} ${g.neckBack.y}`;

  const bust = `${faceContour} C ${g.neckFront.x + 38} 558, 442 574, 481 610 L 110 610 C 151 574, ${g.neckBack.x - 35} 558, ${g.neckBack.x} ${g.neckBack.y} C ${g.gonion.x - 12} ${g.gonion.y + 45}, ${g.gonion.x} ${g.gonion.y + 15}, ${g.gonion.x} ${g.gonion.y} L ${g.ramus.x} ${g.ramus.y} C ${g.ramus.x - 27} ${g.ramus.y - 24}, ${g.skullBack.x - 10} ${g.skullBack.y + 67}, ${g.skullBack.x} ${g.skullBack.y} C ${g.skullBack.x + 4} ${g.skullBack.y - 96}, ${g.crown.x + 61} ${g.crown.y - 17}, ${g.trichion.x} ${g.trichion.y} Z`;

  const hair = `M ${g.trichion.x} ${g.trichion.y}
    C ${g.crown.x + 56} ${g.crown.y - 20}, ${g.skullBack.x - 4} ${g.skullBack.y - 92}, ${g.skullBack.x} ${g.skullBack.y}
    C ${g.skullBack.x + 8} ${g.skullBack.y - 7}, ${g.ramus.x - 14} ${g.ramus.y - 88}, ${g.ramus.x + 6} ${g.ramus.y - 70}
    C ${g.ramus.x + 23} ${g.ramus.y - 95}, ${g.trichion.x - 16} ${g.trichion.y + 17}, ${g.trichion.x} ${g.trichion.y} Z`;

  const landmarks = [g.trichion, g.glabella, g.nasion, g.pronasale, g.subnasale, g.upperLip, g.lowerLip, g.pogonion, g.menton, g.gonion, g.tragion, g.orbitale];

  return (
    <svg viewBox="0 0 600 620" role="img" aria-label={`Profile target face in ${mode} mode`} className="h-auto w-full">
      <defs>
        <linearGradient id="v3ProfileSkin" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#eed7c7" />
          <stop offset="56%" stopColor="#dcb198" />
          <stop offset="100%" stopColor="#c88e74" />
        </linearGradient>
        <linearGradient id="v3ProfileHair" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#292828" />
          <stop offset="100%" stopColor="#49403b" />
        </linearGradient>
        <radialGradient id="v3ProfileLight" cx="64%" cy="34%" r="70%">
          <stop offset="0%" stopColor="#fff7f0" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#6e3428" stopOpacity="0" />
        </radialGradient>
        <filter id="v3ProfileSoft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="8" /></filter>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={bust} fill="url(#v3ProfileSkin)" stroke="#75584c" strokeWidth="1.35" strokeLinejoin="round" />
          <path d={hair} fill="url(#v3ProfileHair)" />
          <ellipse cx={g.tragion.x} cy={g.tragion.y + 31} rx="24" ry="38" fill="#d5a087" stroke="#835d4e" strokeWidth="1" />
          <path d={`M ${g.tragion.x - 3} ${g.tragion.y + 11} C ${g.tragion.x + 14} ${g.tragion.y + 21}, ${g.tragion.x + 13} ${g.tragion.y + 47}, ${g.tragion.x - 3} ${g.tragion.y + 59} C ${g.tragion.x + 4} ${g.tragion.y + 42}, ${g.tragion.x - 9} ${g.tragion.y + 30}, ${g.tragion.x - 3} ${g.tragion.y + 11}`} fill="none" stroke="#996a5a" strokeWidth="1.1" />
          <ellipse cx={g.cheek.x + 8} cy={g.cheek.y + 38} rx="59" ry="48" fill="#98574b" opacity="0.08" filter="url(#v3ProfileSoft)" />
          <ellipse cx={g.cheek.x + 13} cy={g.cheek.y + 24} rx="115" ry="165" fill="url(#v3ProfileLight)" />

          <path d={`M ${g.orbitale.x - 20} ${g.orbitale.y - 3} Q ${g.orbitale.x + 2} ${g.orbitale.y - 12} ${g.orbitale.x + 20} ${g.orbitale.y - 3} Q ${g.orbitale.x + 3} ${g.orbitale.y + 4} ${g.orbitale.x - 20} ${g.orbitale.y - 3} Z`} fill="#fbf7f3" stroke="#55443d" strokeWidth="1.45" />
          <ellipse cx={g.orbitale.x + 2} cy={g.orbitale.y - 2} rx="7" ry="8" fill="#77746c" />
          <circle cx={g.orbitale.x + 3} cy={g.orbitale.y - 1} r="3.6" fill="#252321" />
          <circle cx={g.orbitale.x + 1} cy={g.orbitale.y - 4} r="1.4" fill="#fff" />
          <path d={`M ${g.orbitale.x - 22} ${g.orbitale.y - 24} Q ${g.orbitale.x + 1} ${g.orbitale.y - 35} ${g.orbitale.x + 27} ${g.orbitale.y - 21}`} fill="none" stroke="#443a35" strokeWidth="5.8" strokeLinecap="round" />

          <path d={`M ${g.nasion.x + 2} ${g.nasion.y + 3} C ${g.nasion.x + 29} ${g.nasion.y + 8}, ${g.pronasale.x - 23} ${g.pronasale.y - 11}, ${g.pronasale.x - 2} ${g.pronasale.y}`} fill="none" stroke="#f7e7dc" strokeWidth="1.8" opacity="0.8" />
          <ellipse cx={g.columella.x + 4} cy={g.columella.y + 1} rx="6.8" ry="3.4" fill="#60473e" opacity="0.56" />
          <path d={`M ${g.subnasale.x + 1} ${g.subnasale.y + 3} Q ${g.upperLip.x + 8} ${g.upperLip.y - 7} ${g.upperLip.x} ${g.upperLip.y}`} fill="none" stroke="#955b5f" strokeWidth="3.9" strokeLinecap="round" />
          <path d={`M ${g.stomion.x} ${g.stomion.y} Q ${g.lowerLip.x + 8} ${g.lowerLip.y - 4} ${g.lowerLip.x} ${g.lowerLip.y}`} fill="none" stroke="#ad6b6d" strokeWidth="4.6" strokeLinecap="round" />
          <path d={`M ${g.upperLip.x - 2} ${g.stomion.y} Q ${g.lowerLip.x} ${g.stomion.y + 1} ${g.lowerLip.x + 1} ${g.stomion.y + 1}`} fill="none" stroke="#654047" strokeWidth="1.1" />
          <path d={`M ${g.sulcus.x - 3} ${g.sulcus.y + 2} Q ${g.pogonion.x - 9} ${g.pogonion.y - 28} ${g.pogonion.x - 1} ${g.pogonion.y - 15}`} fill="none" stroke="#9e705f" strokeWidth="1.2" opacity="0.5" />
        </g>
      ) : (
        <g>
          <path d={faceContour} fill="none" stroke="var(--ink)" strokeWidth="1.55" strokeLinecap="round" strokeLinejoin="round" />
          <path d={backContour} fill="none" stroke="var(--ink)" strokeWidth="1.35" strokeLinecap="round" />
          <path d={`M ${g.orbitale.x - 20} ${g.orbitale.y - 3} Q ${g.orbitale.x + 2} ${g.orbitale.y - 12} ${g.orbitale.x + 20} ${g.orbitale.y - 3}`} fill="none" stroke="var(--ink)" strokeWidth="1.35" />
          <ellipse cx={g.tragion.x} cy={g.tragion.y + 31} rx="24" ry="38" fill="none" stroke="var(--ink)" strokeWidth="1.15" />
          <g fill="none" stroke="var(--muted)" strokeWidth="1" strokeDasharray="5 5">
            <line x1={g.tragion.x - 24} y1={g.tragion.y} x2={g.orbitale.x + 165} y2={g.orbitale.y} />
            <line x1={g.nasion.x} y1={g.nasion.y} x2={g.pronasale.x} y2={g.pronasale.y} />
            <line x1={g.pronasale.x} y1={g.pronasale.y} x2={g.pogonion.x} y2={g.pogonion.y} />
            <line x1={g.gonion.x} y1={g.gonion.y} x2={g.menton.x} y2={g.menton.y} />
            <line x1={g.gonion.x} y1={g.gonion.y} x2={g.ramus.x} y2={g.ramus.y} />
          </g>
          {landmarks.map((p, index) => <circle key={index} cx={p.x} cy={p.y} r="3.7" fill="white" stroke="var(--accent)" strokeWidth="1.7" />)}
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

function Toggle<T extends string>({ value, values, onChange, label }: { value: T; values: readonly T[]; onChange: (value: T) => void; label: string }) {
  return <div className="flex border border-[var(--line)] bg-white p-1" role="group" aria-label={label}>{values.map((item) => <button key={item} type="button" onClick={() => onChange(item)} aria-pressed={value === item} className={`px-3 py-2 text-sm capitalize ${value === item ? "bg-[var(--ink)] text-white" : "text-[var(--muted)]"}`}>{item === "rendered" ? "Realistic" : item === "profile" ? "Side" : item}</button>)}</div>;
}

export function IdealReferenceFace() {
  const [view, setView] = useState<View>("front");
  const [mode, setMode] = useState<Mode>("structure");
  const metrics = view === "front" ? FRONT_METRICS : PROFILE_METRICS;

  return (
    <section id="ideal-reference" className="mt-12 border border-[var(--line)] bg-white">
      <div className="border-b border-[var(--line)] p-5 sm:p-7">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--accent)]">Current harmony target</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">The face implied by Mog’s measurements</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--muted)]">Structure exposes the scored anchors and guides. Realistic mode uses those same anchors with smooth anatomical interpolation and restrained portrait shading. Appearance styling never enters the score.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Toggle value={view} values={["front", "profile"] as const} onChange={setView} label="Face view" />
            <Toggle value={mode} values={["structure", "rendered"] as const} onChange={setMode} label="Rendering mode" />
          </div>
        </div>
      </div>
      <div className="grid lg:grid-cols-[minmax(0,1.35fr)_minmax(250px,0.65fr)]">
        <div className="min-h-[520px] border-b border-[var(--line)] bg-[var(--paper)] p-4 sm:p-8 lg:border-b-0 lg:border-r">
          <div className="mx-auto max-w-[560px]">{view === "front" ? <FrontPortrait mode={mode} /> : <ProfilePortrait mode={mode} />}</div>
        </div>
        <div className="p-5 sm:p-7">
          <h3 className="font-semibold">Target centers used in this view</h3>
          <p className="mt-2 text-xs leading-5 text-[var(--muted)]">Every numeric target is read directly from Mog’s neutral harmony reference bands.</p>
          <dl className="mt-5 divide-y divide-[var(--line)] border-y border-[var(--line)]">{metrics.map((metric) => <div key={metric.id} className="flex items-baseline justify-between gap-4 py-2.5 text-sm"><dt className="text-[var(--muted)]">{metric.label}</dt><dd className="font-mono text-xs font-semibold tabular-nums">{display(metric)}</dd></div>)}</dl>
          <p className="mt-5 text-xs leading-5 text-[var(--muted)]">The scored measurements do not uniquely determine hair, skin, shoulders, or every soft-tissue curve. Those are neutral illustration choices; the measured anchors stay identical between modes.</p>
        </div>
      </div>
    </section>
  );
}
