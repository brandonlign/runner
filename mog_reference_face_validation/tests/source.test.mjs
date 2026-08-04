import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync("src/components/methodology/ideal-reference-face-verified.tsx", "utf8");
const geometry = readFileSync("src/lib/analysis/reference-face-geometry.ts", "utf8");
const clay = readFileSync("src/components/methodology/canonical-clay-face.tsx", "utf8");
const mesh = readFileSync("src/components/methodology/gnm-head-mesh.ts", "utf8");

test("the renderer reads the canonical scoring landmarks", () => {
  assert.match(source, /referenceFrontLandmarks/);
  assert.match(source, /referenceProfileLandmarks/);
  assert.match(source, /calculateAnalysisReport\(front, profile, "neutral"\)/);
  assert.doesNotMatch(source, /function frontGeometry\(/);
  assert.doesNotMatch(source, /function profileGeometry\(/);
});

test("front and profile expose exact structure plus a separate clay illustration", () => {
  assert.equal((source.match(/mode === "rendered"/g) ?? []).length, 2);
  assert.match(source, /<FrontReference mode=\{mode\} landmarks=\{front\} \/>/);
  assert.match(source, /<ProfileReference mode=\{mode\} landmarks=\{profile\} \/>/);
  assert.match(source, /Structure mode plots the exact solved scoring landmarks/);
  assert.match(source, /surface vertices and clay shading are illustrative and never enter the harmony score/);
});

test("the canonical front has positive five-degree outward canthal tilt", () => {
  assert.match(geometry, /Math\.cos\(5 \* Math\.PI \/ 180\)/);
  assert.match(geometry, /Math\.sin\(5 \* Math\.PI \/ 180\)/);
  assert.match(source, />\+5° canthal tilt</);
});

test("the profile and front use the production solved coordinates", () => {
  assert.match(geometry, /pronasale: \[0\.203497, 0\.570531\]/);
  assert.match(geometry, /softTissuePogonion: \[0\.05687, 0\.923903\]/);
  assert.match(geometry, /mentolabialSulcus: \[0\.015871, 0\.833935\]/);
  assert.match(geometry, /const faceWidth = 0\.78/);
  assert.match(geometry, /const jawWidth = faceWidth \/ 1\.25/);
});

test("the clay renderer uses the licensed full-head GNM surface", () => {
  assert.match(mesh, /Google GNM v3\.0 head template/);
  assert.match(mesh, /license: "Apache-2\.0"/);
  assert.match(mesh, /vertexCount: GNM_POSITION_DATA\.vertexCount/);
  assert.match(mesh, /triangleCount: 1775/);
  assert.match(clay, /decodeGnmHeadMesh/);
  assert.match(clay, /GNM surface vertices never enter the score/);
  assert.doesNotMatch(clay, /calculateAnalysisReport/);
});

test("unscored measurements remain distinguished from target bands", () => {
  assert.match(source, /Metrics without a defensible comparison convention remain raw measurements/);
});
