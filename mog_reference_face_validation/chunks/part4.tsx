    C ${g.menton.x - 1} ${g.menton.y + 21}, ${g.neckFront.x} ${g.neckFront.y - 17}, ${g.neckFront.x} ${g.neckFront.y}`;

  const backContour = `M ${g.trichion.x} ${g.trichion.y}
    C ${g.crown.x + 54} ${g.crown.y - 20}, ${g.skullBack.x + 4} ${g.skullBack.y - 93}, ${g.skullBack.x} ${g.skullBack.y}
    C ${g.skullBack.x - 10} ${g.skullBack.y + 71}, ${g.ramus.x - 32} ${g.ramus.y - 27}, ${g.ramus.x} ${g.ramus.y}
    L ${g.gonion.x} ${g.gonion.y}
    C ${g.gonion.x - 17} ${g.gonion.y + 51}, ${g.neckBack.x} ${g.neckBack.y - 17}, ${g.neckBack.x} ${g.neckBack.y}`;

  const headFill = `${faceContour}
    L ${g.neckBack.x} ${g.neckBack.y}
    C ${g.gonion.x - 17} ${g.gonion.y + 51}, ${g.gonion.x} ${g.gonion.y + 18}, ${g.gonion.x} ${g.gonion.y}
    L ${g.ramus.x} ${g.ramus.y}
    C ${g.ramus.x - 32} ${g.ramus.y - 27}, ${g.skullBack.x - 10} ${g.skullBack.y + 71}, ${g.skullBack.x} ${g.skullBack.y}
    C ${g.skullBack.x + 4} ${g.skullBack.y - 93}, ${g.crown.x + 54} ${g.crown.y - 20}, ${g.trichion.x} ${g.trichion.y} Z`;

  const hair = `M ${g.trichion.x} ${g.trichion.y}
    C ${g.crown.x + 49} ${g.crown.y - 22}, ${g.skullBack.x - 5} ${g.skullBack.y - 91}, ${g.skullBack.x} ${g.skullBack.y}
    C ${g.skullBack.x + 12} ${g.skullBack.y - 14}, ${g.ramus.x - 12} ${g.ramus.y - 93}, ${g.ramus.x + 7} ${g.ramus.y - 75}
    C ${g.ramus.x + 21} ${g.ramus.y - 101}, ${g.trichion.x - 17} ${g.trichion.y + 20}, ${g.trichion.x} ${g.trichion.y} Z`;

  const points: Array<[string, Point]> = [
    ["trichion", g.trichion], ["glabella", g.glabella], ["nasion", g.nasion],
    ["pronasale", g.pronasale], ["subnasale", g.subnasale], ["upper lip", g.upperLip],
    ["lower lip", g.lowerLip], ["pogonion", g.pogonion], ["menton", g.menton],
    ["gonion", g.gonion], ["tragion", g.tragion], ["orbitale", g.orbitale],
  ];

  return (
    <svg viewBox="0 0 600 600" role="img" aria-label={`Profile target face in ${mode} mode`} className="h-auto w-full">
      <defs>
        <linearGradient id="naturalProfileSkin" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f2d2bd" />
          <stop offset="53%" stopColor="#e7b89d" />
          <stop offset="100%" stopColor="#cf8f76" />
        </linearGradient>
        <linearGradient id="naturalProfileHair" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#2a211e" />
          <stop offset="100%" stopColor="#4a352d" />
        </linearGradient>
        <radialGradient id="naturalProfileCheek" cx="50%" cy="50%" r="60%">
          <stop offset="0%" stopColor="#c87870" stopOpacity="0.34" />
          <stop offset="100%" stopColor="#c87870" stopOpacity="0" />
        </radialGradient>
      </defs>

      {mode === "rendered" ? (
        <g>
          <path d={headFill} fill="url(#naturalProfileSkin)" stroke="#6e5047" strokeWidth="2" strokeLinejoin="round" />
          <path d={hair} fill="url(#naturalProfileHair)" />
          <path d={`M ${g.trichion.x - 7} ${g.trichion.y + 12} C ${g.upperForehead.x - 32} ${g.upperForehead.y + 29}, ${g.cheek.x - 46} ${g.cheek.y + 13}, ${g.gonion.x - 4} ${g.gonion.y + 11} C ${g.neckBack.x + 39} ${g.neckBack.y - 56}, ${g.skullBack.x + 12} ${g.skullBack.y + 45}, ${g.trichion.x - 7} ${g.trichion.y + 12} Z`} fill="#9b5f50" opacity="0.13" />

          <ellipse cx={g.tragion.x - 1} cy={g.tragion.y + 34} rx="27" ry="43" fill="#dfaa90" stroke="#8f6556" strokeWidth="1.4" />
          <path d={`M ${g.tragion.x - 3} ${g.tragion.y + 12} C ${g.tragion.x + 17} ${g.tragion.y + 23}, ${g.tragion.x + 14} ${g.tragion.y + 53}, ${g.tragion.x - 4} ${g.tragion.y + 64} C ${g.tragion.x + 4} ${g.tragion.y + 46}, ${g.tragion.x - 11} ${g.tragion.y + 35}, ${g.tragion.x - 3} ${g.tragion.y + 12}`} fill="none" stroke="#9d6c5c" strokeWidth="1.4" />
          <ellipse cx={g.cheek.x + 12} cy={g.cheek.y + 45} rx="56" ry="42" fill="url(#naturalProfileCheek)" />

          <path d={`M ${g.orbitale.x - 21} ${g.orbitale.y - 4} Q ${g.orbitale.x + 3} ${g.orbitale.y - 14} ${g.orbitale.x + 23} ${g.orbitale.y - 4} Q ${g.orbitale.x + 4} ${g.orbitale.y + 6} ${g.orbitale.x - 21} ${g.orbitale.y - 4} Z`} fill="#fffaf4" stroke="#5d453e" strokeWidth="1.8" />
          <ellipse cx={g.orbitale.x + 4} cy={g.orbitale.y - 3} rx="8" ry="9" fill="#7e6954" />
          <circle cx={g.orbitale.x + 5} cy={g.orbitale.y - 2} r="4" fill="#231c19" />
          <circle cx={g.orbitale.x + 2} cy={g.orbitale.y - 5} r="1.6" fill="#fff" />
          <path d={`M ${g.orbitale.x - 23} ${g.orbitale.y - 26} Q ${g.orbitale.x + 2} ${g.orbitale.y - 39} ${g.orbitale.x + 30} ${g.orbitale.y - 23}`} fill="none" stroke="#49362f" strokeWidth="7" strokeLinecap="round" />

          <path d={`M ${g.nasion.x + 3} ${g.nasion.y + 4} C ${g.nasion.x + 32} ${g.nasion.y + 13}, ${g.pronasale.x - 19} ${g.pronasale.y - 11}, ${g.pronasale.x - 3} ${g.pronasale.y - 1}`} fill="none" stroke="#f6ddcc" strokeWidth="2.2" opacity="0.9" />
          <ellipse cx={g.columella.x + 4} cy={g.columella.y + 2} rx="8" ry="4" fill="#704d45" opacity="0.72" />
          <path d={`M ${g.subnasale.x + 1} ${g.subnasale.y + 4} Q ${g.upperLip.x + 8} ${g.upperLip.y - 8} ${g.upperLip.x} ${g.upperLip.y}`} fill="none" stroke="#9d5f61" strokeWidth="4.5" strokeLinecap="round" />
          <path d={`M ${g.stomion.x} ${g.stomion.y} Q ${g.lowerLip.x + 9} ${g.lowerLip.y - 5} ${g.lowerLip.x} ${g.lowerLip.y}`} fill="none" stroke="#b96f70" strokeWidth="5.3" strokeLinecap="round" />
          <path d={`M ${g.upperLip.x - 3} ${g.stomion.y} Q ${g.lowerLip.x - 1} ${g.stomion.y + 1} ${g.lowerLip.x + 1} ${g.stomion.y + 1}`} fill="none" stroke="#6f4149" strokeWidth="1.4" />
          <path d={`M ${g.sulcus.x - 3} ${g.sulcus.y + 2} Q ${g.pogonion.x - 8} ${g.pogonion.y - 28} ${g.pogonion.x - 1} ${g.pogonion.y - 16}`} fill="none" stroke="#aa7766" strokeWidth="1.5" opacity="0.58" />
          <path d={`M ${g.gonion.x + 4} ${g.gonion.y + 2} Q ${g.menton.x - 20} ${g.menton.y - 9} ${g.menton.x} ${g.menton.y}`} fill="none" stroke="#8b5f51" strokeWidth="2" opacity="0.52" />
        </g>
      ) : (
        <g>
          <path d={faceContour} fill="none" stroke="var(--ink)" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
          <path d={backContour} fill="none" stroke="var(--ink)" strokeWidth="1.5" strokeLinecap="round" />
          <path d={`M ${g.orbitale.x - 21} ${g.orbitale.y - 4} Q ${g.orbitale.x + 3} ${g.orbitale.y - 14} ${g.orbitale.x + 23} ${g.orbitale.y - 4}`} fill="none" stroke="var(--ink)" strokeWidth="1.6" />
          <path d={`M ${g.orbitale.x - 23} ${g.orbitale.y - 26} Q ${g.orbitale.x + 2} ${g.orbitale.y - 39} ${g.orbitale.x + 30} ${g.orbitale.y - 23}`} fill="none" stroke="var(--ink)" strokeWidth="2.2" />
          <ellipse cx={g.tragion.x - 1} cy={g.tragion.y + 34} rx="27" ry="43" fill="none" stroke="var(--ink)" strokeWidth="1.3" />

          <g fill="none" stroke="var(--muted)" strokeWidth="1" strokeDasharray="5 5">
            <line x1={g.tragion.x - 26} y1={g.tragion.y} x2={g.orbitale.x + 165} y2={g.orbitale.y} />
            <line x1={g.nasion.x} y1={g.nasion.y} x2={g.pronasale.x} y2={g.pronasale.y} />
