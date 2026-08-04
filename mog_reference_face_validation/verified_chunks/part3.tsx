          <ellipse cx={rightTragion.x + 1} cy={rightTragion.y + 14} rx="12" ry="31" fill="#d4cbc3" />
          <path d={renderedHeadPath} fill="url(#verifiedFrontClay)" stroke="#9a8e85" strokeWidth="0.58" />
          <path d={renderedHeadPath} fill="url(#verifiedFrontLight)" />

          <ellipse cx={leftPupil.x - 10} cy={leftPupil.y + 58} rx="42" ry="31" fill="#746158" opacity="0.05" filter="url(#verifiedFrontBlur)" />
          <ellipse cx={rightPupil.x + 10} cy={rightPupil.y + 58} rx="42" ry="31" fill="#746158" opacity="0.05" filter="url(#verifiedFrontBlur)" />
          <path d={leftEye} fill="#d8d0c9" fillOpacity="0.16" stroke="#716a65" strokeWidth="0.82" />
          <path d={rightEye} fill="#d8d0c9" fillOpacity="0.16" stroke="#716a65" strokeWidth="0.82" />
          <ellipse cx={leftPupil.x} cy={leftPupil.y} rx="5.4" ry="6.2" fill="#6f6a65" opacity="0.34" />
          <ellipse cx={rightPupil.x} cy={rightPupil.y} rx="5.4" ry="6.2" fill="#6f6a65" opacity="0.34" />

          <path d={smoothOpenPath([leftBrowLateral, leftBrowHigh, leftBrowMedial], 0.16)} fill="none" stroke="#625c57" strokeWidth="2.2" strokeLinecap="round" opacity="0.72" />
          <path d={smoothOpenPath([rightBrowMedial, rightBrowHigh, rightBrowLateral], 0.16)} fill="none" stroke="#625c57" strokeWidth="2.2" strokeLinecap="round" opacity="0.72" />

          <path d={`M ${glabella.x - 3} ${glabella.y + 17} C ${glabella.x - 9} ${leftPupil.y + 30}, ${glabella.x - 10} ${subnasale.y - 24}, ${leftAlare.x + 7} ${leftAlare.y - 7}`} fill="none" stroke="#8d7c72" strokeWidth="1" strokeLinecap="round" opacity="0.55" />
          <path d={`M ${glabella.x + 3} ${glabella.y + 17} C ${glabella.x + 8} ${rightPupil.y + 30}, ${glabella.x + 10} ${subnasale.y - 24}, ${rightAlare.x - 7} ${rightAlare.y - 7}`} fill="none" stroke="#fff" strokeWidth="1.1" strokeLinecap="round" opacity="0.28" />
          <path d={smoothOpenPath([leftAlare, { x: subnasale.x, y: subnasale.y + 3 }, rightAlare], 0.16)} fill="none" stroke="#74675f" strokeWidth="1" />
          <ellipse cx={subnasale.x - 14.5} cy={subnasale.y + 2.2} rx="3.8" ry="1.55" fill="#4f4945" opacity="0.38" />
          <ellipse cx={subnasale.x + 14.5} cy={subnasale.y + 2.2} rx="3.8" ry="1.55" fill="#4f4945" opacity="0.38" />

          <path d={upperLipPath} fill="#9b7f7d" fillOpacity="0.42" />
          <path d={lowerLipPath} fill="#a68a86" fillOpacity="0.42" />
          <path d={`M ${leftMouth.x + 5} ${stomion.y} C ${stomion.x - 19} ${stomion.y + 1}, ${stomion.x + 19} ${stomion.y + 1}, ${rightMouth.x - 5} ${stomion.y}`} fill="none" stroke="#665355" strokeWidth="0.85" />
          <path d={`M ${menton.x - 27} ${menton.y - 26} Q ${menton.x} ${menton.y - 18} ${menton.x + 27} ${menton.y - 26}`} fill="none" stroke="#8f7f74" strokeWidth="0.8" opacity="0.3" />
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
