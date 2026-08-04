import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync("src/components/methodology/ideal-reference-face-verified.tsx", "utf8");
const geometry = readFileSync("src/lib/analysis/reference-face-geometry.ts", "utf8");
const clay = readFileSync("src/components/methodology/canonical-clay-face.tsx", "utf8");
const renders = readFileSync("src/components/methodology/gnm-clay-renders.ts", "utf8");

function readBase64Chunk(fileName, constantName) {
  const file = readFileSync(`src/components/methodology/${fileName}`, "utf8");
  const match = file.match(new RegExp(`export const ${constantName} = "([A-Za-z0-9+/=]+)";`));
  assert.ok(match, `${constantName} must remain one deterministic Base64 string.`);
  return match[1];
}

function assertWebp(buffer, expectedLength) {
  assert.equal(buffer.byteLength, expectedLength);
  assert.equal(buffer.subarray(0, 4).toString("ascii"), "RIFF");
  assert.equal(buffer.subarray(8, 12).toString("ascii"), "WEBP");
}

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
  assert.match(source, /full-resolution neutral Google GNM render fitted to the same frozen geometry/);
  assert.match(source, /illustrative and never enters the harmony score/);
  assert.match(source, /option === "rendered" \? "Clay"/);
});

test("the canonical front has positive five-degree outward canthal tilt", () => {
  assert.match(geometry, /Math\.cos\(5 \* Math\.PI \/ 180\)/);
  assert.match(geometry, /Math\.sin\(5 \* Math\.PI \/ 180\)/);
  assert.match(source, />\+5° canthal tilt</);
});

test("the profile is the GNM-regularized solved coordinate set", () => {
  assert.match(geometry, /pronasale: \[0\.1488, 0\.56235\]/);
  assert.match(geometry, /softTissuePogonion: \[0\.02255, 0\.94177\]/);
  assert.match(geometry, /mentolabialSulcus: \[0\.00617, 0\.87921\]/);
  assert.match(geometry, /gonion: \[-0\.35752, 0\.88602\]/);
  assert.match(geometry, /Google GNM mean/);
  assert.match(geometry, /const faceWidth = 0\.78/);
  assert.match(geometry, /const jawWidth = faceWidth \/ 1\.25/);
});

test("clay mode uses deterministic licensed full-resolution GNM snapshots", () => {
  assert.match(clay, /GNM_FRONT_WEBP/);
  assert.match(clay, /GNM_PROFILE_WEBP/);
  assert.match(clay, /GNM_REFERENCE_GEOMETRY_REVISION/);
  assert.match(clay, /<image/);
  assert.match(clay, /href=\{href\}/);
  assert.match(clay, /width="600"/);
  assert.match(clay, /height="620"/);
  assert.match(clay, /all scoring continues to use the separate canonical semantic landmarks/);
  assert.doesNotMatch(clay, /calculateAnalysisReport/);
  assert.match(renders, /Apache-2\.0/);
  assert.match(renders, /Google GNM v3\.0/);
  assert.match(renders, /gnm-neutral-v2/);
  assert.match(renders, /reference-face-geometry\.ts/);
});

test("the vendored WebP chunks reconstruct exact uncorrupted images", () => {
  const frontBase64 = [1, 2, 3, 4, 5]
    .map((part) => readBase64Chunk(`gnm-clay-front-${part}.ts`, `GNM_CLAY_FRONT_${part}`))
    .join("");
  const profileBase64 = [1, 2, 3]
    .map((part) => readBase64Chunk(`gnm-clay-profile-${part}.ts`, `GNM_CLAY_PROFILE_${part}`))
    .join("");
  assertWebp(Buffer.from(frontBase64, "base64"), 14_888);
  assertWebp(Buffer.from(profileBase64, "base64"), 7_122);
  assert.match(renders, /GNM_CLAY_FRONT_1 \+/);
  assert.match(renders, /GNM_CLAY_PROFILE_1 \+/);
  assert.match(renders, /data:image\/webp;base64/);
});

test("clay mode removes legacy anatomy layers", () => {
  assert.doesNotMatch(source, /<path d=\{shoulders\} fill=/);
  assert.doesNotMatch(source, /M 112 620 C 170 574/);
});

test("unscored measurements remain distinguished from target bands", () => {
  assert.match(source, /Metrics without a defensible comparison convention remain raw measurements/);
});
