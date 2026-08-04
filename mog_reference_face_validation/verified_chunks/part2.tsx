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

  const facePath = smoothClosedPath([
    trichion,
    rightTemple,
    rightCheek,
    rightJaw,
    menton,
    leftJaw,
    leftCheek,
    leftTemple,
  ], 0.115);

  // Trichion is the hairline, not the top of the skull. Rendered mode infers a
  // continuous scalp above it while the structure view remains landmark-exact.
  const renderedHeadPath = `M ${trichion.x} 13
    C ${trichion.x + 92} 12, ${leftTemple.x + 10} ${leftTemple.y - 62}, ${leftTemple.x} ${leftTemple.y}
    C ${leftTemple.x + 8} ${leftTemple.y + 54}, ${leftCheek.x + 4} ${leftCheek.y - 38}, ${leftCheek.x} ${leftCheek.y}
    C ${leftCheek.x + 4} ${leftCheek.y + 62}, ${leftJaw.x + 10} ${leftJaw.y - 28}, ${leftJaw.x} ${leftJaw.y}
    C ${leftJaw.x - 9} ${menton.y - 35}, ${menton.x + 54} ${menton.y - 4}, ${menton.x} ${menton.y}
    C ${menton.x - 54} ${menton.y - 4}, ${rightJaw.x + 9} ${menton.y - 35}, ${rightJaw.x} ${rightJaw.y}
    C ${rightJaw.x - 10} ${rightJaw.y - 28}, ${rightCheek.x - 4} ${rightCheek.y + 62}, ${rightCheek.x} ${rightCheek.y}
    C ${rightCheek.x - 4} ${rightCheek.y - 38}, ${rightTemple.x - 8} ${rightTemple.y + 54}, ${rightTemple.x} ${rightTemple.y}
    C ${rightTemple.x - 10} ${rightTemple.y - 62}, ${trichion.x - 92} 12, ${trichion.x} 13 Z`;

  const neckPath = smoothClosedPath([
    { x: menton.x - 51, y: menton.y - 11 },
    { x: menton.x - 57, y: menton.y + 21 },
    { x: menton.x - 68, y: 578 },
    { x: menton.x + 68, y: 578 },
    { x: menton.x + 57, y: menton.y + 21 },
    { x: menton.x + 51, y: menton.y - 11 },
  ], 0.12);
  const shoulders = "M 68 620 C 132 574, 218 571, 244 555 C 269 581, 331 581, 356 555 C 382 571, 468 574, 532 620 Z";

  const upperLipPath = `M ${leftMouth.x} ${stomion.y}
    C ${leftMouth.x + 18} ${upperLip.y + 1}, ${upperLip.x - 16} ${upperLip.y - 2}, ${upperLip.x} ${upperLip.y}
    C ${upperLip.x + 16} ${upperLip.y - 2}, ${rightMouth.x - 18} ${upperLip.y + 1}, ${rightMouth.x} ${stomion.y}
    C ${rightMouth.x - 22} ${stomion.y + 2}, ${leftMouth.x + 22} ${stomion.y + 2}, ${leftMouth.x} ${stomion.y} Z`;
  const lowerLipPath = `M ${leftMouth.x} ${stomion.y}
    C ${leftMouth.x + 18} ${lowerLip.y - 1}, ${lowerLip.x - 17} ${lowerLip.y + 3}, ${lowerLip.x} ${lowerLip.y}
    C ${lowerLip.x + 17} ${lowerLip.y + 3}, ${rightMouth.x - 18} ${lowerLip.y - 1}, ${rightMouth.x} ${stomion.y}
    C ${rightMouth.x - 23} ${stomion.y + 1}, ${leftMouth.x + 23} ${stomion.y + 1}, ${leftMouth.x} ${stomion.y} Z`;

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
        <linearGradient id="verifiedFrontClay" x1="0.12" y1="0" x2="0.9" y2="1">
          <stop offset="0%" stopColor="#f4f0eb" />
          <stop offset="52%" stopColor="#ddd5ce" />
          <stop offset="100%" stopColor="#b9aca2" />
        </linearGradient>
        <radialGradient id="verifiedFrontLight" cx="42%" cy="28%" r="76%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.42" />
          <stop offset="68%" stopColor="#ffffff" stopOpacity="0" />
          <stop offset="100%" stopColor="#66574e" stopOpacity="0.12" />
        </radialGradient>
        <filter id="verifiedFrontBlur" x="-35%" y="-35%" width="170%" height="170%"><feGaussianBlur stdDeviation="10" /></filter>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={shoulders} fill="#c5c0bb" />
          <path d={neckPath} fill="url(#verifiedFrontClay)" />
          <ellipse cx={leftTragion.x - 1} cy={leftTragion.y + 14} rx="12" ry="31" fill="#d4cbc3" />
