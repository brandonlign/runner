import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync("src/components/methodology/ideal-reference-face-verified.tsx", "utf8");
const geometry = readFileSync("src/lib/analysis/reference-face-geometry.ts", "utf8");

test("the renderer reads the canonical scoring landmarks", () => {
  assert.match(source, /referenceFrontLandmarks/);
  assert.match(source, /referenceProfileLandmarks/);
  assert.match(source, /calculateAnalysisReport\(front, profile, "neutral"\)/);
  assert.doesNotMatch(source, /function frontGeometry\(/);
  assert.doesNotMatch(source, /function profileGeometry\(/);
});

test("front and profile structure share anchors with rendered mode", () => {
  assert.equal((source.match(/mode === "rendered"/g) ?? []).length, 2);
  assert.match(source, /<FrontReference mode=\{mode\} landmarks=\{front\} \/>/);
  assert.match(source, /<ProfileReference mode=\{mode\} landmarks=\{profile\} \/>/);
  assert.match(source, /Structure and realistic modes use the exact same solved landmarks/);
});

test("the canonical front has positive five-degree outward canthal tilt", () => {
  assert.match(geometry, /Math\.cos\(5 \* Math\.PI \/ 180\)/);
  assert.match(geometry, /Math\.sin\(5 \* Math\.PI \/ 180\)/);
  assert.match(source, />\+5° canthal tilt</);
});

test("the profile and front use the production solved coordinates", () => {
  assert.match(geometry, /pronasale: \[0\.203497, 0\.570531\]/);
  assert.match(geometry, /softTissuePogonion: \[0\.05687, 0\.923903\]/);
  assert.match(geometry, /const faceWidth = 0\.78/);
  assert.match(geometry, /const jawWidth = faceWidth \/ 1\.25/);
});

test("illustrative styling is explicitly excluded from scoring", () => {
  assert.match(source, /none of those illustrative details enters the harmony score/);
  assert.match(source, /Metrics without a defensible comparison convention remain raw measurements/);
});
