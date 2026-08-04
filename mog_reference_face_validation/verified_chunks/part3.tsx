        <g>
          <path d={shoulders} fill="#c6c0ba" />
          <path d={neckPath} fill="url(#verifiedFrontClay)" />
          <ellipse cx={leftTragion.x - 1} cy={leftTragion.y + 14} rx="12" ry="31" fill="#d4cbc3" />
          <ellipse cx={rightTragion.x + 1} cy={rightTragion.y + 14} rx="12" ry="31" fill="#d4cbc3" />
          <g filter="url(#verifiedFrontMeshShadow)">
            <CanonicalClayFace view="front" landmarks={landmarks} />
          </g>
        </g>
      ) : (
        <g>
          <path d={facePath} fill="none" stroke="var(--ink)" strokeWidth="1.55" />
          <path d={leftEye} fill="none" stroke="var(--ink)" strokeWidth="1.35" />
          <path d={rightEye} fill="none" stroke="var(--ink)" strokeWidth="1.35" />
          <path d={smoothOpenPath([leftBrowLateral, leftBrowHigh, leftBrowMedial], 0.16)} fill="none" stroke="var(--ink)" strokeWidth="1.9" />
          <path d={smoothOpenPath([rightBrowMedial, rightBrowHigh, rightBrowLateral], 0.16)} fill="none" stroke="var(--ink)" strokeWidth="1.9" />
          <path d={`M ${glabella.x} ${glabella.y + 14} L ${subnasale.x} ${subnasale.y - 14} M ${leftAlare.x} ${leftAlare.y} Q ${subnasale.x} ${subnasale.y + 6} ${rightAlare.x} ${rightAlare.y}`} fill="none" stroke="var(--ink)" strokeWidth="1.35" />
          <path d={upperLipPath} fill="none" stroke="var(--ink)" strokeWidth="1.15" />
          <path d={lowerLipPath} fill="none" stroke="var(--ink)" strokeWidth="1.15" />
          <g fill="none" stroke="var(--muted)" strokeWidth="1" strokeDasharray="5 5">
            <line x1="88" y1={trichion.y} x2="512" y2={trichion.y} />
            <line x1="88" y1={glabella.y} x2="512" y2={glabella.y} />
            <line x1="88" y1={subnasale.y} x2="512" y2={subnasale.y} />
            <line x1="88" y1={menton.y} x2="512" y2={menton.y} />
            <line x1={trichion.x} y1="24" x2={menton.x} y2={menton.y + 22} />
            <line x1={leftCheek.x} y1={leftCheek.y} x2={rightCheek.x} y2={rightCheek.y} />
            <line x1={leftJaw.x} y1={leftJaw.y} x2={rightJaw.x} y2={rightJaw.y} />
            <line x1={leftOuter.x} y1={leftOuter.y} x2={leftInner.x} y2={leftInner.y} />
            <line x1={rightInner.x} y1={rightInner.y} x2={rightOuter.x} y2={rightOuter.y} />
            <line x1={leftAlare.x} y1={leftAlare.y} x2={rightAlare.x} y2={rightAlare.y} />
            <line x1={leftMouth.x} y1={stomion.y} x2={rightMouth.x} y2={stomion.y} />
          </g>
          {structureIds.map((id) => {
            const point = q(id);
            return <circle key={id} cx={point.x} cy={point.y} r="3.7" fill="white" stroke="var(--accent)" strokeWidth="1.7"><title>{id}</title></circle>;
          })}
          <g fill="var(--muted)" fontSize="11">
            <text x="96" y={trichion.y - 7}>upper third</text>
            <text x="96" y={glabella.y - 7}>middle third</text>
            <text x="96" y={subnasale.y - 7}>lower third</text>
            <text x={rightOuter.x + 10} y={rightOuter.y - 7}>+5° canthal tilt</text>
          </g>
        </g>
      )}
    </svg>
  );
}

function ProfileReference({ mode, landmarks }: { mode: RenderMode; landmarks: FacialLandmarks }) {
  const q = (id: LandmarkId) => profileMap(requiredPoint(landmarks, id));
  const trichion = q("trichion");
  const upperForehead = q("upperForehead");
  const glabella = q("glabella");
  const nasion = q("nasion");
  const pronasale = q("pronasale");
  const columella = q("columella");
  const subnasale = q("subnasale");
  const upperLip = q("labialeSuperius");
  const stomion = q("stomion");
  const lowerLip = q("labialeInferius");
  const sulcus = q("mentolabialSulcus");
  const pogonion = q("softTissuePogonion");
  const menton = q("menton");
  const gonion = q("gonion");
  const ramus = q("ramusPoint");
  const cervical = q("cervicalPoint");
  const throat = q("throatPoint");
  const tragion = q("tragion");
  const orbitale = q("orbitale");
  const cheek = q("cheekProjection");

  const skullBack: SvgPoint = { x: 145, y: 190 };
  const crown: SvgPoint = { x: 230, y: 28 };
  const neckBack: SvgPoint = { x: 205, y: 560 };
  const neckFront: SvgPoint = { x: 350, y: 560 };

  const bridgeMid: SvgPoint = {
    x: nasion.x + (pronasale.x - nasion.x) * 0.46,
    y: nasion.y + (pronasale.y - nasion.y) * 0.43 - 5,
  };
  const tipApproach: SvgPoint = { x: pronasale.x - 17, y: pronasale.y - 8 };
  const lowerLipTransition: SvgPoint = { x: lowerLip.x - 3, y: lowerLip.y + 18 };

  // The sulcus is a crease, not an outer-silhouette point. Keeping it inside
  // the face removes the artificial chin spike while retaining the exact
  // measured location for structure mode and the mentolabial guide.
  const faceContour = `M ${trichion.x} ${trichion.y}
    C ${trichion.x + 4} ${trichion.y + 24}, ${upperForehead.x - 8} ${upperForehead.y - 19}, ${upperForehead.x} ${upperForehead.y}
