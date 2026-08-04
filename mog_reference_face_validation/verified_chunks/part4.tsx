    C ${upperForehead.x + 8} ${upperForehead.y + 24}, ${glabella.x - 10} ${glabella.y - 18}, ${glabella.x} ${glabella.y}
    C ${glabella.x + 2} ${glabella.y + 10}, ${nasion.x + 4} ${nasion.y - 10}, ${nasion.x} ${nasion.y}
    C ${nasion.x + 20} ${nasion.y + 20}, ${bridgeMid.x - 13} ${bridgeMid.y - 17}, ${bridgeMid.x} ${bridgeMid.y}
    C ${bridgeMid.x + 27} ${bridgeMid.y + 15}, ${tipApproach.x - 13} ${tipApproach.y - 5}, ${tipApproach.x} ${tipApproach.y}
    C ${tipApproach.x + 10} ${tipApproach.y + 5}, ${pronasale.x - 7} ${pronasale.y - 3}, ${pronasale.x} ${pronasale.y}
    C ${pronasale.x - 5} ${pronasale.y + 7}, ${columella.x + 12} ${columella.y - 4}, ${columella.x} ${columella.y}
    C ${columella.x - 12} ${columella.y + 2}, ${subnasale.x + 11} ${subnasale.y - 3}, ${subnasale.x} ${subnasale.y}
    C ${subnasale.x + 2} ${subnasale.y + 23}, ${upperLip.x + 2} ${upperLip.y - 14}, ${upperLip.x} ${upperLip.y}
    C ${upperLip.x + 5} ${upperLip.y + 5}, ${stomion.x + 5} ${stomion.y - 4}, ${stomion.x} ${stomion.y}
    C ${stomion.x + 4} ${stomion.y + 10}, ${lowerLip.x + 6} ${lowerLip.y - 9}, ${lowerLip.x} ${lowerLip.y}
    C ${lowerLip.x + 2} ${lowerLip.y + 8}, ${lowerLipTransition.x + 3} ${lowerLipTransition.y - 5}, ${lowerLipTransition.x} ${lowerLipTransition.y}
    C ${lowerLipTransition.x - 4} ${lowerLipTransition.y + 24}, ${pogonion.x + 10} ${pogonion.y - 23}, ${pogonion.x} ${pogonion.y}
    C ${pogonion.x + 4} ${pogonion.y + 17}, ${menton.x + 10} ${menton.y - 13}, ${menton.x} ${menton.y}
    C ${menton.x - 4} ${menton.y + 16}, ${neckFront.x + 2} ${neckFront.y - 18}, ${neckFront.x} ${neckFront.y}`;

  const backContour = `M ${trichion.x} ${trichion.y}
    C ${trichion.x - 20} ${trichion.y - 25}, ${crown.x + 48} ${crown.y - 14}, ${crown.x} ${crown.y}
    C ${crown.x - 56} ${crown.y + 2}, ${skullBack.x - 3} ${skullBack.y - 69}, ${skullBack.x} ${skullBack.y}
    C ${skullBack.x - 5} ${skullBack.y + 52}, ${tragion.x - 17} ${tragion.y - 7}, ${tragion.x} ${tragion.y}
    C ${tragion.x - 7} ${tragion.y + 38}, ${ramus.x - 4} ${ramus.y - 28}, ${ramus.x} ${ramus.y}
    C ${ramus.x - 2} ${ramus.y + 43}, ${gonion.x - 6} ${gonion.y - 30}, ${gonion.x} ${gonion.y}
    C ${gonion.x - 8} ${gonion.y + 36}, ${neckBack.x - 3} ${neckBack.y - 19}, ${neckBack.x} ${neckBack.y}`;

  const bustPath = `${faceContour}
    C ${neckFront.x + 43} 573, 452 590, 512 620
    L 88 620
    C 148 590, ${neckBack.x - 43} 573, ${neckBack.x} ${neckBack.y}
    C ${gonion.x - 8} ${gonion.y + 36}, ${gonion.x} ${gonion.y + 13}, ${gonion.x} ${gonion.y}
    C ${gonion.x - 6} ${gonion.y - 30}, ${ramus.x - 2} ${ramus.y + 43}, ${ramus.x} ${ramus.y}
    C ${ramus.x - 4} ${ramus.y - 28}, ${tragion.x - 7} ${tragion.y + 38}, ${tragion.x} ${tragion.y}
    C ${tragion.x - 17} ${tragion.y - 7}, ${skullBack.x - 5} ${skullBack.y + 52}, ${skullBack.x} ${skullBack.y}
    C ${skullBack.x - 3} ${skullBack.y - 69}, ${crown.x - 56} ${crown.y + 2}, ${crown.x} ${crown.y}
    C ${crown.x + 48} ${crown.y - 14}, ${trichion.x - 20} ${trichion.y - 25}, ${trichion.x} ${trichion.y} Z`;

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
        <radialGradient id="verifiedProfileLight" cx="72%" cy="28%" r="76%">
          <stop offset="0%" stopColor="#fff" stopOpacity="0.42" />
          <stop offset="68%" stopColor="#fff" stopOpacity="0" />
          <stop offset="100%" stopColor="#67584f" stopOpacity="0.12" />
        </radialGradient>
        <filter id="verifiedProfileBlur" x="-35%" y="-35%" width="170%" height="170%"><feGaussianBlur stdDeviation="10" /></filter>
        <filter id="verifiedProfileMeshShadow" x="-20%" y="-20%" width="150%" height="150%">
          <feDropShadow dx="3" dy="10" stdDeviation="11" floodColor="#6e6259" floodOpacity="0.14" />
        </filter>
      </defs>

      {mode === "rendered" ? (
        <g filter="url(#verifiedProfileMeshShadow)">
          <CanonicalClayFace view="profile" landmarks={landmarks} />
        </g>
      ) : (
        <g>
          <path d={faceContour} fill="none" stroke="var(--ink)" strokeWidth="1.55" strokeLinecap="round" strokeLinejoin="round" />
          <path d={backContour} fill="none" stroke="var(--ink)" strokeWidth="1.35" strokeLinecap="round" />
          <path d={`M ${orbitale.x - 18} ${orbitale.y - 2} Q ${orbitale.x + 1} ${orbitale.y - 9} ${orbitale.x + 16} ${orbitale.y - 2}`} fill="none" stroke="var(--ink)" strokeWidth="1.3" />
          <ellipse cx={tragion.x} cy={tragion.y + 29} rx="20" ry="34" fill="none" stroke="var(--ink)" strokeWidth="1.1" />
          <g fill="none" stroke="var(--muted)" strokeWidth="1" strokeDasharray="5 5">
            <line x1={tragion.x - 22} y1={tragion.y} x2={orbitale.x + 155} y2={orbitale.y} />
            <line x1={nasion.x} y1={nasion.y} x2={pronasale.x} y2={pronasale.y} />
            <line x1={pronasale.x} y1={pronasale.y} x2={pogonion.x} y2={pogonion.y} />
            <line x1={subnasale.x} y1={subnasale.y} x2={pogonion.x} y2={pogonion.y} />
            <line x1={gonion.x} y1={gonion.y} x2={menton.x} y2={menton.y} />
            <line x1={gonion.x} y1={gonion.y} x2={ramus.x} y2={ramus.y} />
            <line x1={menton.x} y1={menton.y} x2={cervical.x} y2={cervical.y} />
            <line x1={cervical.x} y1={cervical.y} x2={throat.x} y2={throat.y} />
          </g>
          {structureIds.map((id) => {
            const point = q(id);
            return <circle key={id} cx={point.x} cy={point.y} r="3.7" fill="white" stroke="var(--accent)" strokeWidth="1.7"><title>{id}</title></circle>;
          })}
          <g fill="var(--muted)" fontSize="11">
            <text x={tragion.x - 4} y={tragion.y - 11}>Frankfort plane</text>
            <text x={pronasale.x + 9} y={pronasale.y - 5}>tip</text>
            <text x={pogonion.x + 9} y={pogonion.y}>pogonion</text>
            <text x={gonion.x - 53} y={gonion.y - 9}>gonion</text>
