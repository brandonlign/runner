import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const source = readFileSync("src/components/methodology/ideal-reference-face-v3.tsx", "utf8");

test("front geometry enforces positive canthal tilt", () => {
  assert.match(source, /const rise = Math\.tan\(target\("front-average-canthal", 5\)/);
  assert.match(source, /leftInner = \{ x: g\.cx - g\.innerGap \/ 2, y: g\.eyeY \+ g\.rise \/ 2 \}/);
  assert.match(source, /leftOuter = \{ x: leftInner\.x - g\.eyeWidth, y: g\.eyeY - g\.rise \/ 2 \}/);
  assert.match(source, /rightOuter = \{ x: rightInner\.x \+ g\.eyeWidth, y: g\.eyeY - g\.rise \/ 2 \}/);
  assert.match(source, />positive canthal tilt</);
});

test("profile columella moves down and back from the tip", () => {
  assert.match(source, /const columella = \{ x: pronasale\.x - 25, y: pronasale\.y \+ 21 \+ \(tipRotation - 100\) \* 0\.12 \}/);
});

test("structure and realistic modes share one geometry definition per view", () => {
  assert.equal((source.match(/function frontGeometry\(/g) ?? []).length, 1);
  assert.equal((source.match(/function profileGeometry\(/g) ?? []).length, 1);
  assert.match(source, /<FrontPortrait mode=\{mode\} \/>/);
  assert.match(source, /<ProfilePortrait mode=\{mode\} \/>/);
  assert.equal((source.match(/mode === "rendered"/g) ?? []).length, 2);
});

test("target values come from the scoring bands", () => {
  assert.match(source, /getReferenceBand\(id, "neutral"\)/);
  assert.match(source, /Every numeric target is read directly from Mog’s neutral harmony reference bands/);
});

test("portrait styling is not a scoring input", () => {
  assert.match(source, /Appearance styling never enters the score/);
  assert.match(source, /the measured anchors stay identical between modes/);
});
