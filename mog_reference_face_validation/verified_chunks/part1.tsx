"use client";

import { useMemo, useState } from "react";
import { CanonicalClayFace } from "./canonical-clay-face";
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

function smoothOpenPath(points: SvgPoint[], tension = 0.14): string {
  if (points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;

  let path = `M ${points[0].x} ${points[0].y}`;
  for (let index = 0; index < points.length - 1; index += 1) {
    const p0 = points[index - 1] ?? points[index];
    const p1 = points[index];
    const p2 = points[index + 1];
    const p3 = points[index + 2] ?? p2;
    const c1 = {
      x: p1.x + (p2.x - p0.x) * tension,
      y: p1.y + (p2.y - p0.y) * tension,
    };
    const c2 = {
      x: p2.x - (p3.x - p1.x) * tension,
      y: p2.y - (p3.y - p1.y) * tension,
    };
    path += ` C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${p2.x} ${p2.y}`;
  }
  return path;
}

function smoothClosedPath(points: SvgPoint[], tension = 0.12): string {
  if (points.length < 3) return smoothOpenPath(points, tension);

  let path = `M ${points[0].x} ${points[0].y}`;
  for (let index = 0; index < points.length; index += 1) {
    const p0 = points[(index - 1 + points.length) % points.length];
    const p1 = points[index];
    const p2 = points[(index + 1) % points.length];
    const p3 = points[(index + 2) % points.length];
    const c1 = {
      x: p1.x + (p2.x - p0.x) * tension,
      y: p1.y + (p2.y - p0.y) * tension,
    };
    const c2 = {
      x: p2.x - (p3.x - p1.x) * tension,
      y: p2.y - (p3.y - p1.y) * tension,
    };
    path += ` C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${p2.x} ${p2.y}`;
  }
  return `${path} Z`;
}

function eyePath(inner: SvgPoint, outer: SvgPoint, height: number): string {
  const centerX = (inner.x + outer.x) / 2;
  const upperY = Math.min(inner.y, outer.y) - height * 0.5;
  const lowerY = Math.max(inner.y, outer.y) + height * 0.36;
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
