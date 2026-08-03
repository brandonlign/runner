          <ellipse cx={subnasale.x - 15} cy={subnasale.y + 2.5} rx="4.1" ry="1.9" fill="#514b47" opacity="0.46" />
          <ellipse cx={subnasale.x + 15} cy={subnasale.y + 2.5} rx="4.1" ry="1.9" fill="#514b47" opacity="0.46" />

          <path d={upperLipPath} fill="#967575" opacity="0.9" />
          <path d={lowerLipPath} fill="#ab8380" opacity="0.9" />
          <path d={`M ${leftMouth.x + 4} ${stomion.y} Q ${stomion.x} ${stomion.y + 1.5} ${rightMouth.x - 4} ${stomion.y}`} fill="none" stroke="#5f4d4e" strokeWidth="1" />
          <path d={`M ${menton.x - 29} ${menton.y - 27} Q ${menton.x} ${menton.y - 18} ${menton.x + 29} ${menton.y - 27}`} fill="none" stroke="#8e7c70" strokeWidth="0.95" opacity="0.38" />
        </g>
      ) : (
        <g>
          <path d={facePath} fill="none" stroke="var(--ink)" strokeWidth="1.55" />
          <path d={leftEye} fill="none" stroke="var(--ink)" strokeWidth="1.35" />
          <path d={rightEye} fill="none" stroke="var(--ink)" strokeWidth="1.35" />
          <path d={`M ${leftBrowLateral.x} ${leftBrowLateral.y} Q ${leftBrowHigh.x} ${leftBrowHigh.y - 3} ${leftBrowMedial.x} ${leftBrowMedial.y}`} fill="none" stroke="var(--ink)" strokeWidth="1.9" />
          <path d={`M ${rightBrowMedial.x} ${rightBrowMedial.y} Q ${rightBrowHigh.x} ${rightBrowHigh.y - 3} ${rightBrowLateral.x} ${rightBrowLateral.y}`} fill="none" stroke="var(--ink)" strokeWidth="1.9" />
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

  const faceContour = `M ${trichion.x} ${trichion.y}
    C ${upperForehead.x - 9} ${upperForehead.y - 30}, ${upperForehead.x + 1} ${upperForehead.y - 7}, ${upperForehead.x} ${upperForehead.y}
    C ${upperForehead.x + 4} ${upperForehead.y + 27}, ${glabella.x + 4} ${glabella.y - 12}, ${glabella.x} ${glabella.y}
    Q ${nasion.x - 7} ${nasion.y - 6} ${nasion.x} ${nasion.y}
    C ${nasion.x + 19} ${nasion.y + 8}, ${pronasale.x - 30} ${pronasale.y - 22}, ${pronasale.x - 4} ${pronasale.y - 7}
