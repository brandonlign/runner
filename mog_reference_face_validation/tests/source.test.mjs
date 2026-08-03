import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const rendererPath = "src/components/methodology/ideal-reference-face-natural.tsx";
const source = readFileSync(rendererPath, "utf8");

test("front geometry enforces positive canthal tilt", () => {
  assert.match(source, /const rise = Math\.tan\(target\("front-average-canthal", 5\)/);
  assert.match(source, /leftInner = \{ x: g\.centerX - g\.innerGap \/ 2, y: g\.eyeY \+ g\.rise \/ 2 \}/);
  assert.match(source, /leftOuter = \{ x: leftInner\.x - g\.eyeWidth, y: g\.eyeY - g\.rise \/ 2 \}/);
  assert.match(source, /rightOuter = \{ x: rightInner\.x \+ g\.eyeWidth, y: g\.eyeY - g\.rise \/ 2 \}/);
  assert.match(source, />positive canthal tilt</);
});

test("profile columella moves down and back from the tip in screen coordinates", () => {
  assert.match(source, /const columella = \{ x: pronasale\.x - 26, y: pronasale\.y \+ 22 \+ \(tipRotation - 100\) \* 0\.12 \}/);
  assert.doesNotMatch(source, /tipRotation \+ 180/);
});

test("structure and realistic modes share one geometry definition per view", () => {
  assert.equal((source.match(/function frontGeometry\(/g) ?? []).length, 1);
  assert.equal((source.match(/function profileGeometry\(/g) ?? []).length, 1);
  assert.match(source, /<FrontFace mode=\{mode\} \/>/);
  assert.match(source, /<ProfileFace mode=\{mode\} \/>/);
  assert.equal((source.match(/mode === "rendered"/g) ?? []).length, 2);
});

test("all displayed target values come from scoring reference bands", () => {
  assert.match(source, /getReferenceBand\(id, "neutral"\)/);
  assert.match(source, /Every numeric target comes directly from the neutral harmony reference bands/);
});

test("rendering style is explicitly excluded from scoring", () => {
  assert.match(source, /Styling never enters the score/);
  assert.match(source, /Those elements are illustrative only; the scored structure remains unchanged between modes/);
});
