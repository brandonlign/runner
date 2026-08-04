  };
  const tipApproach: SvgPoint = { x: pronasale.x - 17, y: pronasale.y - 8 };
  const lowerLipTransition: SvgPoint = { x: lowerLip.x - 3, y: lowerLip.y + 18 };

  // The sulcus is a crease, not an outer-silhouette point. Keeping it inside
  // the face removes the artificial chin spike while retaining the exact
  // measured location for structure mode and the mentolabial guide.
  const faceContour = `M ${trichion.x} ${trichion.y}
    C ${trichion.x + 4} ${trichion.y + 24}, ${upperForehead.x - 8} ${upperForehead.y - 19}, ${upperForehead.x} ${upperForehead.y}
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
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={bustPath} fill="url(#verifiedProfileClay)" stroke="#9a8e85" strokeWidth="0.58" strokeLinejoin="round" />
          <path d={bustPath} fill="url(#verifiedProfileLight)" />
          <ellipse cx={tragion.x} cy={tragion.y + 29} rx="18" ry="32" fill="#d3c9c0" />
          <path d={`M ${tragion.x - 3} ${tragion.y + 10} C ${tragion.x + 10} ${tragion.y + 20}, ${tragion.x + 9} ${tragion.y + 42}, ${tragion.x - 3} ${tragion.y + 52} C ${tragion.x + 2} ${tragion.y + 38}, ${tragion.x - 7} ${tragion.y + 28}, ${tragion.x - 3} ${tragion.y + 10}`} fill="none" stroke="#8b7d73" strokeWidth="0.8" opacity="0.72" />
          <ellipse cx={cheek.x + 5} cy={cheek.y + 34} rx="54" ry="42" fill="#715f56" opacity="0.05" filter="url(#verifiedProfileBlur)" />

          <path d={`M ${orbitale.x - 17} ${orbitale.y - 2} Q ${orbitale.x + 1} ${orbitale.y - 7} ${orbitale.x + 15} ${orbitale.y - 2}`} fill="none" stroke="#716a65" strokeWidth="0.9" />
          <ellipse cx={orbitale.x} cy={orbitale.y - 0.4} rx="4.5" ry="5.2" fill="#6f6a65" opacity="0.3" />
          <path d={`M ${orbitale.x - 19} ${orbitale.y - 21} Q ${orbitale.x} ${orbitale.y - 27} ${orbitale.x + 21} ${orbitale.y - 18}`} fill="none" stroke="#625c57" strokeWidth="2.15" strokeLinecap="round" opacity="0.72" />

          <path d={smoothOpenPath([nasion, bridgeMid, tipApproach, pronasale], 0.11)} fill="none" stroke="#fff" strokeWidth="1.05" opacity="0.27" />
          <ellipse cx={columella.x + 3} cy={columella.y + 1} rx="4.6" ry="2.2" fill="#504a46" opacity="0.34" />
          <path d={smoothOpenPath([subnasale, upperLip, stomion], 0.13)} fill="none" stroke="#9b7f7d" strokeWidth="2.55" strokeLinecap="round" opacity="0.58" />
          <path d={smoothOpenPath([stomion, lowerLip], 0.13)} fill="none" stroke="#a68a86" strokeWidth="2.9" strokeLinecap="round" opacity="0.58" />
          <path d={`M ${upperLip.x - 2} ${stomion.y} Q ${lowerLip.x} ${stomion.y + 1} ${lowerLip.x + 1} ${stomion.y + 1}`} fill="none" stroke="#665355" strokeWidth="0.75" opacity="0.72" />
          <path d={`M ${sulcus.x - 9} ${sulcus.y} Q ${sulcus.x} ${sulcus.y + 4} ${sulcus.x + 7} ${sulcus.y - 2}`} fill="none" stroke="#8f7f74" strokeWidth="0.8" opacity="0.3" />
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
