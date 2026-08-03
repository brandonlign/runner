import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import test from "node:test";

const rendererPath = "src/components/methodology/ideal-reference-face-natural.tsx";
const source = readFileSync(rendererPath, "utf8");

test("assembled renderer mirror is frozen", () => {
  const blob = execFileSync("git", ["hash-object", rendererPath], { encoding: "utf8" }).trim();
  assert.equal(blob, "11c70ed2bab8d8728bfc89a5aac53c70531c5495");
});

test("front geometry explicitly uses positive canthal tilt", () => {
  assert.match(source, /Positive canthal tilt/);
  assert.match(source, /leftOuter: Point = \{ x: leftInner\.x - g\.eyeWidth, y: g\.eyeY - g\.canthalRise \/ 2 \}/);
  assert.match(source, /rightOuter: Point = \{ x: rightInner\.x \+ g\.eyeWidth, y: g\.eyeY - g\.canthalRise \/ 2 \}/);
});

test("profile uses corrected screen-coordinate columella direction", () => {
  assert.match(source, /tipToColumellaAngle = 135 \+ \(tipRotation - 100\) \* 0\.2/);
  assert.doesNotMatch(source, /tipRotation \+ 180/);
});

test("structure and realistic modes share one geometry source", () => {
  assert.equal((source.match(/function frontGeometry\(/g) ?? []).length, 1);
  assert.equal((source.match(/function profileGeometry\(/g) ?? []).length, 1);
  assert.match(source, /<FrontFace mode=\{mode\} \/>/);
  assert.match(source, /<ProfileFace mode=\{mode\} \/>/);
});
