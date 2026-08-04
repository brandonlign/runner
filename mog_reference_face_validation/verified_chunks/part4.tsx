    y: pogonion.y + (menton.y - pogonion.y) * 0.55,
  };

  const facialContourPoints: SvgPoint[] = [
    trichion,
    upperForehead,
    glabella,
    nasion,
    bridgeMid,
    tipApproach,
    pronasale,
    columella,
    subnasale,
    upperLip,
    stomion,
    lowerLip,
    sulcus,
    pogonion,
    chinTransition,
    menton,
    neckFront,
  ];
  const faceContour = smoothOpenPath(facialContourPoints, 0.105);
  const backContourPoints: SvgPoint[] = [trichion, crown, skullBack, tragion, ramus, gonion, neckBack];
  const backContour = smoothOpenPath(backContourPoints, 0.12);

  const bustPath = smoothClosedPath([
    ...facialContourPoints,
    { x: 418, y: 581 },
    { x: 510, y: 620 },
    { x: 90, y: 620 },
    { x: 157, y: 581 },
    ...backContourPoints.slice().reverse(),
  ], 0.07);

  const hairPath = smoothClosedPath([
    trichion,
    crown,
    skullBack,
    { x: tragion.x - 10, y: tragion.y - 20 },
    { x: tragion.x + 3, y: tragion.y - 45 },
    { x: trichion.x - 18, y: trichion.y + 20 },
  ], 0.1);

  const structureIds: LandmarkId[] = [
    "trichion", "upperForehead", "glabella", "nasion", "pronasale",
    "columella", "subnasale", "labialeSuperius", "labialeInferius",
    "mentolabialSulcus", "softTissuePogonion", "menton", "gonion",
    "ramusPoint", "tragion", "orbitale", "cervicalPoint", "throatPoint",
  ];

  return (
    <svg viewBox="0 0 600 620" role="img" aria-label={`Profile target face in ${mode} mode`} className="h-auto w-full">
      <defs>
        <linearGradient id="verifiedProfileClay" x1="0.05" y1="0" x2="0.9" y2="1">
          <stop offset="0%" stopColor="#f4f0eb" />
          <stop offset="55%" stopColor="#ddd3cb" />
          <stop offset="100%" stopColor="#b7a99f" />
        </linearGradient>
        <linearGradient id="verifiedProfileHair" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#3c3936" />
          <stop offset="100%" stopColor="#5a544f" />
        </linearGradient>
        <radialGradient id="verifiedProfileLight" cx="72%" cy="28%" r="76%">
          <stop offset="0%" stopColor="#fff" stopOpacity="0.42" />
          <stop offset="68%" stopColor="#fff" stopOpacity="0" />
          <stop offset="100%" stopColor="#67584f" stopOpacity="0.12" />
        </radialGradient>
        <filter id="verifiedProfileBlur" x="-35%" y="-35%" width="170%" height="170%"><feGaussianBlur stdDeviation="10" /></filter>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={bustPath} fill="url(#verifiedProfileClay)" stroke="#91857d" strokeWidth="0.65" strokeLinejoin="round" />
          <path d={bustPath} fill="url(#verifiedProfileLight)" />
          <path d={hairPath} fill="url(#verifiedProfileHair)" opacity="0.96" />
          <ellipse cx={tragion.x} cy={tragion.y + 29} rx="19" ry="33" fill="#d0c5bc" />
          <path d={`M ${tragion.x - 3} ${tragion.y + 10} C ${tragion.x + 11} ${tragion.y + 20}, ${tragion.x + 10} ${tragion.y + 43}, ${tragion.x - 3} ${tragion.y + 53} C ${tragion.x + 2} ${tragion.y + 39}, ${tragion.x - 8} ${tragion.y + 28}, ${tragion.x - 3} ${tragion.y + 10}`} fill="none" stroke="#8b7d73" strokeWidth="0.9" />
          <ellipse cx={cheek.x + 6} cy={cheek.y + 36} rx="55" ry="43" fill="#715f56" opacity="0.055" filter="url(#verifiedProfileBlur)" />

          <path d={`M ${orbitale.x - 18} ${orbitale.y - 2} Q ${orbitale.x + 1} ${orbitale.y - 8} ${orbitale.x + 16} ${orbitale.y - 2} Q ${orbitale.x + 2} ${orbitale.y + 2} ${orbitale.x - 18} ${orbitale.y - 2} Z`} fill="#f7f5f2" fillOpacity="0.88" stroke="#595450" strokeWidth="0.95" />
          <ellipse cx={orbitale.x} cy={orbitale.y - 0.5} rx="5" ry="5.8" fill="#77736d" />
          <circle cx={orbitale.x + 0.8} cy={orbitale.y} r="2.6" fill="#302e2c" />
          <circle cx={orbitale.x - 0.4} cy={orbitale.y - 2.4} r="0.9" fill="white" />
          <path d={`M ${orbitale.x - 20} ${orbitale.y - 21} Q ${orbitale.x} ${orbitale.y - 28} ${orbitale.x + 22} ${orbitale.y - 18}`} fill="none" stroke="#4c4844" strokeWidth="4.1" strokeLinecap="round" />

          <path d={smoothOpenPath([nasion, bridgeMid, tipApproach, pronasale], 0.11)} fill="none" stroke="#fff" strokeWidth="1.15" opacity="0.3" />
          <ellipse cx={columella.x + 3} cy={columella.y + 1} rx="5" ry="2.45" fill="#504a46" opacity="0.42" />
          <path d={smoothOpenPath([subnasale, upperLip, stomion], 0.13)} fill="none" stroke="#9b7b7b" strokeWidth="3" strokeLinecap="round" />
          <path d={smoothOpenPath([stomion, lowerLip], 0.13)} fill="none" stroke="#aa8683" strokeWidth="3.5" strokeLinecap="round" />
          <path d={`M ${upperLip.x - 2} ${stomion.y} Q ${lowerLip.x} ${stomion.y + 1} ${lowerLip.x + 1} ${stomion.y + 1}`} fill="none" stroke="#665355" strokeWidth="0.85" />
          <path d={smoothOpenPath([sulcus, { x: pogonion.x - 8, y: pogonion.y - 22 }, pogonion], 0.12)} fill="none" stroke="#8f7f74" strokeWidth="0.85" opacity="0.32" />
        </g>
      ) : (
        <g>
          <path d={faceContour} fill="none" stroke="var(--ink)" strokeWidth="1.55" strokeLinecap="round" strokeLinejoin="round" />
          <path d={backContour} fill="none" stroke="var(--ink)" strokeWidth="1.35" strokeLinecap="round" />
          <path d={`M ${orbitale.x - 18} ${orbitale.y - 2} Q ${orbitale.x + 1} ${orbitale.y - 9} ${orbitale.x + 16} ${orbitale.y - 2}`} fill="none" stroke="var(--ink)" strokeWidth="1.3" />
          <ellipse cx={tragion.x} cy={tragion.y + 29} rx="20" ry="34" fill="none" stroke="var(--ink)" strokeWidth="1.1" />
          <g fill="none" stroke="var(--muted)" strokeWidth="1" strokeDasharray="5 5">
