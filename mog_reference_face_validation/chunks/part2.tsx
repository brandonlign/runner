  // Positive canthal tilt: outer corners are visually higher than inner corners.
  const leftInner: Point = { x: g.centerX - g.innerGap / 2, y: g.eyeY + g.canthalRise / 2 };
  const rightInner: Point = { x: g.centerX + g.innerGap / 2, y: g.eyeY + g.canthalRise / 2 };
  const leftOuter: Point = { x: leftInner.x - g.eyeWidth, y: g.eyeY - g.canthalRise / 2 };
  const rightOuter: Point = { x: rightInner.x + g.eyeWidth, y: g.eyeY - g.canthalRise / 2 };
  const leftEye = eyePath(leftInner, leftOuter, g.eyeHeight);
  const rightEye = eyePath(rightInner, rightOuter, g.eyeHeight);

  const noseLeft = g.centerX - g.noseWidth / 2;
  const noseRight = g.centerX + g.noseWidth / 2;
  const mouthLeft = g.centerX - g.mouthWidth / 2;
  const mouthRight = g.centerX + g.mouthWidth / 2;
  const browY = g.eyeY - g.eyeWidth * target("front-eyebrow-height", 0.42) - 7;
  const upperLipY = g.mouthY - g.lipHeight * g.upperLipShare;
  const lowerLipY = g.mouthY + g.lipHeight * (1 - g.upperLipShare);

  const face = `M ${leftTemple + 18} ${g.hairlineY + 6}
    C ${leftTemple - 15} ${g.hairlineY + 55}, ${leftCheek - 15} ${g.glabellaY + 36}, ${leftCheek} ${g.subnasaleY - 17}
    C ${leftCheek + 4} ${g.subnasaleY + 54}, ${leftJaw - 7} ${g.mouthY + 50}, ${leftJaw} ${g.chinY - 55}
    C ${leftJaw + 30} ${g.chinY - 13}, ${g.centerX - 38} ${g.chinY}, ${g.centerX} ${g.chinY}
    C ${g.centerX + 38} ${g.chinY}, ${rightJaw - 30} ${g.chinY - 13}, ${rightJaw} ${g.chinY - 55}
    C ${rightJaw + 7} ${g.mouthY + 50}, ${rightCheek - 4} ${g.subnasaleY + 54}, ${rightCheek} ${g.subnasaleY - 17}
    C ${rightCheek + 15} ${g.glabellaY + 36}, ${rightTemple + 15} ${g.hairlineY + 55}, ${rightTemple - 18} ${g.hairlineY + 6}
    Q ${g.centerX} ${g.hairlineY - 13} ${leftTemple + 18} ${g.hairlineY + 6} Z`;

  const hair = `M ${leftTemple + 10} ${g.hairlineY + 18}
    C ${leftTemple - 18} ${g.hairlineY - 28}, ${g.centerX - 118} 42, ${g.centerX} 38
    C ${g.centerX + 118} 42, ${rightTemple + 18} ${g.hairlineY - 28}, ${rightTemple - 10} ${g.hairlineY + 18}
    C ${g.centerX + 76} ${g.hairlineY - 5}, ${g.centerX + 32} ${g.hairlineY + 4}, ${g.centerX} ${g.hairlineY + 18}
    C ${g.centerX - 32} ${g.hairlineY + 4}, ${g.centerX - 76} ${g.hairlineY - 5}, ${leftTemple + 10} ${g.hairlineY + 18} Z`;

  const upperLip = `M ${mouthLeft} ${g.mouthY} Q ${g.centerX - 28} ${upperLipY - 3} ${g.centerX} ${upperLipY + 1} Q ${g.centerX + 28} ${upperLipY - 3} ${mouthRight} ${g.mouthY} Q ${g.centerX} ${g.mouthY + 2} ${mouthLeft} ${g.mouthY} Z`;
  const lowerLip = `M ${mouthLeft} ${g.mouthY} Q ${g.centerX} ${lowerLipY + 5} ${mouthRight} ${g.mouthY} Q ${g.centerX} ${g.mouthY + 3} ${mouthLeft} ${g.mouthY} Z`;

  const points: Array<[string, Point]> = [
    ["trichion", { x: g.centerX, y: g.hairlineY }],
    ["glabella", { x: g.centerX, y: g.glabellaY }],
    ["subnasale", { x: g.centerX, y: g.subnasaleY }],
    ["menton", { x: g.centerX, y: g.chinY }],
    ["left zygion", { x: leftCheek, y: g.subnasaleY - 17 }],
    ["right zygion", { x: rightCheek, y: g.subnasaleY - 17 }],
    ["left gonion", { x: leftJaw, y: g.chinY - 55 }],
    ["right gonion", { x: rightJaw, y: g.chinY - 55 }],
    ["left pupil", { x: leftPupil, y: g.eyeY }],
    ["right pupil", { x: rightPupil, y: g.eyeY }],
    ["left alare", { x: noseLeft, y: g.subnasaleY - 2 }],
    ["right alare", { x: noseRight, y: g.subnasaleY - 2 }],
    ["left cheilion", { x: mouthLeft, y: g.mouthY }],
    ["right cheilion", { x: mouthRight, y: g.mouthY }],
  ];

  return (
    <svg viewBox="0 0 600 600" role="img" aria-label={`Front target face in ${mode} mode`} className="h-auto w-full">
      <defs>
        <linearGradient id="naturalFrontSkin" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f4d7c3" />
          <stop offset="52%" stopColor="#e9bea4" />
          <stop offset="100%" stopColor="#d89d81" />
        </linearGradient>
        <linearGradient id="naturalFrontHair" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#2b211d" />
          <stop offset="100%" stopColor="#49352d" />
        </linearGradient>
        <radialGradient id="naturalFrontCheek" cx="50%" cy="45%" r="60%">
          <stop offset="0%" stopColor="#d98f83" stopOpacity="0.32" />
          <stop offset="100%" stopColor="#d98f83" stopOpacity="0" />
        </radialGradient>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={hair} fill="url(#naturalFrontHair)" />
          <ellipse cx={leftCheek - 7} cy={g.eyeY + 87} rx="21" ry="48" fill="url(#naturalFrontSkin)" stroke="#815f53" strokeWidth="1.4" />
          <ellipse cx={rightCheek + 7} cy={g.eyeY + 87} rx="21" ry="48" fill="url(#naturalFrontSkin)" stroke="#815f53" strokeWidth="1.4" />
          <path d={face} fill="url(#naturalFrontSkin)" stroke="#6e5047" strokeWidth="2" />
          <path d={`M ${leftTemple + 10} ${g.hairlineY + 30} C ${leftCheek - 12} ${g.glabellaY + 70}, ${leftJaw - 12} ${g.mouthY + 36}, ${g.centerX - 82} ${g.chinY - 30} C ${g.centerX - 126} ${g.chinY - 58}, ${g.centerX - 164} ${g.subnasaleY + 42}, ${leftTemple + 10} ${g.hairlineY + 30} Z`} fill="#9a5f50" opacity="0.13" />
          <path d={`M ${rightTemple - 10} ${g.hairlineY + 30} C ${rightCheek + 12} ${g.glabellaY + 70}, ${rightJaw + 12} ${g.mouthY + 36}, ${g.centerX + 82} ${g.chinY - 30} C ${g.centerX + 126} ${g.chinY - 58}, ${g.centerX + 164} ${g.subnasaleY + 42}, ${rightTemple - 10} ${g.hairlineY + 30} Z`} fill="#9a5f50" opacity="0.13" />
          <ellipse cx={leftPupil - 7} cy={g.eyeY + 73} rx="48" ry="34" fill="url(#naturalFrontCheek)" />
          <ellipse cx={rightPupil + 7} cy={g.eyeY + 73} rx="48" ry="34" fill="url(#naturalFrontCheek)" />
