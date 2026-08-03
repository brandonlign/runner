    Q ${pronasale.x + 7} ${pronasale.y} ${pronasale.x} ${pronasale.y + 7}
    Q ${columella.x + 9} ${columella.y - 3} ${columella.x} ${columella.y}
    Q ${subnasale.x + 7} ${subnasale.y - 2} ${subnasale.x} ${subnasale.y}
    Q ${upperLip.x + 10} ${upperLip.y - 6} ${upperLip.x} ${upperLip.y}
    Q ${stomion.x + 5} ${stomion.y - 1} ${stomion.x} ${stomion.y}
    Q ${lowerLip.x + 9} ${lowerLip.y - 1} ${lowerLip.x} ${lowerLip.y}
    Q ${sulcus.x - 5} ${sulcus.y - 1} ${sulcus.x} ${sulcus.y}
    C ${sulcus.x + 6} ${sulcus.y + 15}, ${pogonion.x + 12} ${pogonion.y - 14}, ${pogonion.x} ${pogonion.y}
    Q ${menton.x + 17} ${menton.y} ${menton.x} ${menton.y}
    C ${menton.x - 2} ${menton.y + 17}, ${neckFront.x} ${neckFront.y - 14}, ${neckFront.x} ${neckFront.y}`;

  const backContour = `M ${trichion.x} ${trichion.y}
    C ${crown.x + 55} ${crown.y - 7}, ${skullBack.x + 2} ${skullBack.y - 91}, ${skullBack.x} ${skullBack.y}
    C ${skullBack.x - 6} ${skullBack.y + 60}, ${tragion.x - 10} ${tragion.y + 25}, ${ramus.x} ${ramus.y}
    L ${gonion.x} ${gonion.y}
    C ${gonion.x - 9} ${gonion.y + 36}, ${neckBack.x} ${neckBack.y - 14}, ${neckBack.x} ${neckBack.y}`;

  const bustPath = `${faceContour}
    C ${neckFront.x + 45} 571, 445 585, 505 620
    L 90 620
    C 150 585, ${neckBack.x - 42} 571, ${neckBack.x} ${neckBack.y}
    C ${gonion.x - 9} ${gonion.y + 36}, ${gonion.x} ${gonion.y + 12}, ${gonion.x} ${gonion.y}
    L ${ramus.x} ${ramus.y}
    C ${tragion.x - 10} ${tragion.y + 25}, ${skullBack.x - 6} ${skullBack.y + 60}, ${skullBack.x} ${skullBack.y}
    C ${skullBack.x + 2} ${skullBack.y - 91}, ${crown.x + 55} ${crown.y - 7}, ${trichion.x} ${trichion.y} Z`;

  const hairPath = `M ${trichion.x} ${trichion.y}
    C ${crown.x + 51} ${crown.y - 11}, ${skullBack.x - 2} ${skullBack.y - 88}, ${skullBack.x} ${skullBack.y}
    C ${skullBack.x + 2} ${skullBack.y + 28}, ${tragion.x - 12} ${tragion.y - 19}, ${tragion.x + 3} ${tragion.y - 44}
    C ${tragion.x + 20} ${tragion.y - 70}, ${trichion.x - 19} ${trichion.y + 20}, ${trichion.x} ${trichion.y} Z`;

  const structureIds: LandmarkId[] = [
    "trichion", "upperForehead", "glabella", "nasion", "pronasale",
    "columella", "subnasale", "labialeSuperius", "labialeInferius",
    "mentolabialSulcus", "softTissuePogonion", "menton", "gonion",
    "ramusPoint", "tragion", "orbitale", "cervicalPoint", "throatPoint",
  ];

  return (
    <svg viewBox="0 0 600 620" role="img" aria-label={`Profile target face in ${mode} mode`} className="h-auto w-full">
      <defs>
        <linearGradient id="verifiedProfileClay" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f0ebe4" />
          <stop offset="56%" stopColor="#d7cbc0" />
          <stop offset="100%" stopColor="#b8a79a" />
        </linearGradient>
        <linearGradient id="verifiedProfileHair" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#343434" />
          <stop offset="100%" stopColor="#59534e" />
        </linearGradient>
        <radialGradient id="verifiedProfileLight" cx="68%" cy="28%" r="75%">
          <stop offset="0%" stopColor="#fff" stopOpacity="0.43" />
          <stop offset="70%" stopColor="#fff" stopOpacity="0" />
          <stop offset="100%" stopColor="#6a5a50" stopOpacity="0.14" />
        </radialGradient>
        <filter id="verifiedProfileBlur" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="9" /></filter>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={bustPath} fill="url(#verifiedProfileClay)" stroke="#83776e" strokeWidth="0.8" strokeLinejoin="round" />
          <path d={hairPath} fill="url(#verifiedProfileHair)" />
          <path d={bustPath} fill="url(#verifiedProfileLight)" />
          <ellipse cx={tragion.x} cy={tragion.y + 29} rx="20" ry="34" fill="#cec1b6" />
          <path d={`M ${tragion.x - 3} ${tragion.y + 10} C ${tragion.x + 12} ${tragion.y + 20}, ${tragion.x + 11} ${tragion.y + 43}, ${tragion.x - 3} ${tragion.y + 54} C ${tragion.x + 3} ${tragion.y + 39}, ${tragion.x - 8} ${tragion.y + 28}, ${tragion.x - 3} ${tragion.y + 10}`} fill="none" stroke="#89796d" strokeWidth="1" />
          <ellipse cx={cheek.x + 7} cy={cheek.y + 36} rx="55" ry="43" fill="#725f55" opacity="0.07" filter="url(#verifiedProfileBlur)" />

          <path d={`M ${orbitale.x - 18} ${orbitale.y - 2} Q ${orbitale.x + 1} ${orbitale.y - 9} ${orbitale.x + 16} ${orbitale.y - 2} Q ${orbitale.x + 2} ${orbitale.y + 3} ${orbitale.x - 18} ${orbitale.y - 2} Z`} fill="#fbfaf8" stroke="#4b4947" strokeWidth="1.2" />
          <ellipse cx={orbitale.x} cy={orbitale.y - 1} rx="5.5" ry="6.5" fill="#74716a" />
          <circle cx={orbitale.x + 1} cy={orbitale.y} r="3" fill="#282725" />
          <circle cx={orbitale.x - 0.5} cy={orbitale.y - 2.8} r="1.1" fill="white" />
          <path d={`M ${orbitale.x - 20} ${orbitale.y - 21} Q ${orbitale.x} ${orbitale.y - 29} ${orbitale.x + 22} ${orbitale.y - 18}`} fill="none" stroke="#474440" strokeWidth="4.6" strokeLinecap="round" />

          <path d={`M ${nasion.x + 2} ${nasion.y + 3} C ${nasion.x + 22} ${nasion.y + 8}, ${pronasale.x - 25} ${pronasale.y - 15}, ${pronasale.x - 2} ${pronasale.y}`} fill="none" stroke="#fff" strokeWidth="1.35" opacity="0.38" />
          <ellipse cx={columella.x + 3} cy={columella.y + 1} rx="5.5" ry="2.8" fill="#504a46" opacity="0.5" />
          <path d={`M ${subnasale.x + 1} ${subnasale.y + 2} Q ${upperLip.x + 7} ${upperLip.y - 5} ${upperLip.x} ${upperLip.y}`} fill="none" stroke="#967575" strokeWidth="3.2" strokeLinecap="round" />
          <path d={`M ${stomion.x} ${stomion.y} Q ${lowerLip.x + 7} ${lowerLip.y - 3} ${lowerLip.x} ${lowerLip.y}`} fill="none" stroke="#aa8380" strokeWidth="3.8" strokeLinecap="round" />
          <path d={`M ${upperLip.x - 2} ${stomion.y} Q ${lowerLip.x} ${stomion.y + 1} ${lowerLip.x + 1} ${stomion.y + 1}`} fill="none" stroke="#5d4c4c" strokeWidth="1" />
          <path d={`M ${sulcus.x - 3} ${sulcus.y + 2} Q ${pogonion.x - 8} ${pogonion.y - 25} ${pogonion.x - 1} ${pogonion.y - 14}`} fill="none" stroke="#8e7c70" strokeWidth="1.05" opacity="0.42" />
        </g>
