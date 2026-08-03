          <path d={leftEye} fill="#fffaf4" stroke="#5d453e" strokeWidth="2" />
          <path d={rightEye} fill="#fffaf4" stroke="#5d453e" strokeWidth="2" />
          <ellipse cx={leftPupil} cy={g.eyeY - 1} rx="10" ry="12" fill="#7e6954" />
          <ellipse cx={rightPupil} cy={g.eyeY - 1} rx="10" ry="12" fill="#7e6954" />
          <circle cx={leftPupil} cy={g.eyeY} r="5" fill="#231c19" />
          <circle cx={rightPupil} cy={g.eyeY} r="5" fill="#231c19" />
          <circle cx={leftPupil - 3} cy={g.eyeY - 4} r="2" fill="#fff" />
          <circle cx={rightPupil - 3} cy={g.eyeY - 4} r="2" fill="#fff" />

          <path d={`M ${leftPupil - g.eyeWidth * 0.56} ${browY + 8} Q ${leftPupil - 7} ${browY - 7} ${leftPupil + g.eyeWidth * 0.58} ${browY + 2}`} fill="none" stroke="#49362f" strokeWidth="8" strokeLinecap="round" />
          <path d={`M ${rightPupil - g.eyeWidth * 0.58} ${browY + 2} Q ${rightPupil + 7} ${browY - 7} ${rightPupil + g.eyeWidth * 0.56} ${browY + 8}`} fill="none" stroke="#49362f" strokeWidth="8" strokeLinecap="round" />

          <path d={`M ${g.centerX - 7} ${g.glabellaY + 20} C ${g.centerX - 15} ${g.eyeY + 40}, ${g.centerX - 19} ${g.subnasaleY - 38}, ${noseLeft + 8} ${g.subnasaleY - 8}`} fill="none" stroke="#a8715e" strokeWidth="2.2" strokeLinecap="round" opacity="0.75" />
          <path d={`M ${g.centerX + 7} ${g.glabellaY + 20} C ${g.centerX + 15} ${g.eyeY + 40}, ${g.centerX + 19} ${g.subnasaleY - 38}, ${noseRight - 8} ${g.subnasaleY - 8}`} fill="none" stroke="#f6ddcc" strokeWidth="2" strokeLinecap="round" opacity="0.9" />
          <path d={`M ${noseLeft} ${g.subnasaleY - 2} Q ${g.centerX - 24} ${g.subnasaleY + 9} ${g.centerX} ${g.subnasaleY + 4} Q ${g.centerX + 24} ${g.subnasaleY + 9} ${noseRight} ${g.subnasaleY - 2}`} fill="none" stroke="#895e50" strokeWidth="2" strokeLinecap="round" />
          <ellipse cx={g.centerX - 19} cy={g.subnasaleY + 4} rx="6" ry="3" fill="#704d45" opacity="0.7" />
          <ellipse cx={g.centerX + 19} cy={g.subnasaleY + 4} rx="6" ry="3" fill="#704d45" opacity="0.7" />

          <path d={upperLip} fill="#aa6366" />
          <path d={lowerLip} fill="#bf7a7b" />
          <path d={`M ${mouthLeft + 4} ${g.mouthY} Q ${g.centerX} ${g.mouthY + 3} ${mouthRight - 4} ${g.mouthY}`} fill="none" stroke="#6e4149" strokeWidth="1.4" />
          <path d={`M ${g.centerX - 34} ${g.chinY - 28} Q ${g.centerX} ${g.chinY - 15} ${g.centerX + 34} ${g.chinY - 28}`} fill="none" stroke="#b9826f" strokeWidth="1.4" opacity="0.55" />
        </g>
      ) : (
        <g>
          <path d={face} fill="none" stroke="var(--ink)" strokeWidth="1.7" />
          <path d={leftEye} fill="none" stroke="var(--ink)" strokeWidth="1.5" />
          <path d={rightEye} fill="none" stroke="var(--ink)" strokeWidth="1.5" />
          <path d={`M ${leftPupil - g.eyeWidth * 0.56} ${browY + 8} Q ${leftPupil - 7} ${browY - 7} ${leftPupil + g.eyeWidth * 0.58} ${browY + 2}`} fill="none" stroke="var(--ink)" strokeWidth="2.2" />
          <path d={`M ${rightPupil - g.eyeWidth * 0.58} ${browY + 2} Q ${rightPupil + 7} ${browY - 7} ${rightPupil + g.eyeWidth * 0.56} ${browY + 8}`} fill="none" stroke="var(--ink)" strokeWidth="2.2" />
          <path d={`M ${g.centerX} ${g.glabellaY + 16} L ${g.centerX} ${g.subnasaleY - 13} M ${noseLeft} ${g.subnasaleY - 2} Q ${g.centerX} ${g.subnasaleY + 9} ${noseRight} ${g.subnasaleY - 2}`} fill="none" stroke="var(--ink)" strokeWidth="1.5" />
          <path d={upperLip} fill="none" stroke="var(--ink)" strokeWidth="1.3" />
          <path d={lowerLip} fill="none" stroke="var(--ink)" strokeWidth="1.3" />

          <g fill="none" stroke="var(--muted)" strokeWidth="1" strokeDasharray="5 5">
            <line x1={92} y1={g.hairlineY} x2={508} y2={g.hairlineY} />
            <line x1={92} y1={g.glabellaY} x2={508} y2={g.glabellaY} />
            <line x1={92} y1={g.subnasaleY} x2={508} y2={g.subnasaleY} />
            <line x1={92} y1={g.chinY} x2={508} y2={g.chinY} />
            <line x1={g.centerX} y1={60} x2={g.centerX} y2={556} />
            <line x1={leftCheek} y1={g.subnasaleY - 17} x2={rightCheek} y2={g.subnasaleY - 17} />
            <line x1={leftJaw} y1={g.chinY - 55} x2={rightJaw} y2={g.chinY - 55} />
            <line x1={leftPupil} y1={g.eyeY} x2={rightPupil} y2={g.eyeY} />
            <line x1={leftOuter.x} y1={leftOuter.y} x2={leftInner.x} y2={leftInner.y} />
            <line x1={rightInner.x} y1={rightInner.y} x2={rightOuter.x} y2={rightOuter.y} />
            <line x1={noseLeft} y1={g.subnasaleY - 2} x2={noseRight} y2={g.subnasaleY - 2} />
            <line x1={mouthLeft} y1={g.mouthY} x2={mouthRight} y2={g.mouthY} />
          </g>

          {points.map(([name, point]) => (
            <circle key={name} cx={point.x} cy={point.y} r="4" fill="white" stroke="var(--accent)" strokeWidth="2"><title>{name}</title></circle>
          ))}
          <g fill="var(--muted)" fontSize="11">
            <text x="103" y={g.hairlineY - 7}>upper third</text>
            <text x="103" y={g.glabellaY - 7}>middle third</text>
            <text x="103" y={g.subnasaleY - 7}>lower third</text>
            <text x={rightOuter.x + 12} y={rightOuter.y - 7}>positive canthal tilt</text>
          </g>
        </g>
      )}
    </svg>
  );
}

function ProfileFace({ mode }: { mode: RenderMode }) {
  const g = useMemo(profileGeometry, []);

  const faceContour = `M ${g.trichion.x} ${g.trichion.y}
    C ${g.upperForehead.x - 5} ${g.upperForehead.y - 31}, ${g.upperForehead.x + 3} ${g.upperForehead.y - 9}, ${g.upperForehead.x} ${g.upperForehead.y}
    C ${g.upperForehead.x + 6} ${g.upperForehead.y + 27}, ${g.glabella.x + 7} ${g.glabella.y - 14}, ${g.glabella.x} ${g.glabella.y}
    Q ${g.nasion.x - 9} ${g.nasion.y - 8} ${g.nasion.x} ${g.nasion.y}
    C ${g.nasion.x + 30} ${g.nasion.y + 10}, ${g.pronasale.x - 20} ${g.pronasale.y - 14}, ${g.pronasale.x} ${g.pronasale.y}
    Q ${g.columella.x + 13} ${g.columella.y - 7} ${g.columella.x} ${g.columella.y}
    Q ${g.subnasale.x + 8} ${g.subnasale.y - 3} ${g.subnasale.x} ${g.subnasale.y}
    Q ${g.upperLip.x + 10} ${g.upperLip.y - 6} ${g.upperLip.x} ${g.upperLip.y}
    Q ${g.stomion.x + 6} ${g.stomion.y - 1} ${g.stomion.x} ${g.stomion.y}
    Q ${g.lowerLip.x + 11} ${g.lowerLip.y - 2} ${g.lowerLip.x} ${g.lowerLip.y}
    Q ${g.sulcus.x - 5} ${g.sulcus.y - 2} ${g.sulcus.x} ${g.sulcus.y}
    Q ${g.pogonion.x + 15} ${g.pogonion.y - 13} ${g.pogonion.x} ${g.pogonion.y}
    Q ${g.menton.x + 21} ${g.menton.y + 1} ${g.menton.x} ${g.menton.y}
