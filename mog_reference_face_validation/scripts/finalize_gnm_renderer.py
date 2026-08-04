from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text()
    if new in content:
        print(f"already finalized: {path}")
        return
    count = content.count(old)
    if count != 1:
        raise RuntimeError(f"expected one replacement in {path}, found {count}")
    path.write_text(content.replace(old, new, 1))
    print(f"finalized: {path}")


replace_once(
    ROOT / "src/components/methodology/canonical-clay-face.tsx",
    '    <g aria-label={`Google GNM neutral clay ${view} illustration`}>\n      {projection.faces.map(({ face, points, fill }, index) => (',
    '    <g aria-label={`Google GNM neutral clay ${view} illustration`}>\n'
    '      <rect x="-100" y="-100" width="800" height="820" fill="var(--paper)" />\n'
    '      {projection.faces.map(({ face, points, fill }, index) => (',
)

replace_once(
    ROOT / "verified_chunks/part3.tsx",
    '''        <g>
          <path d={shoulders} fill="#c6c0ba" />
          <path d={neckPath} fill="url(#verifiedFrontClay)" />
          <ellipse cx={leftTragion.x - 1} cy={leftTragion.y + 14} rx="12" ry="31" fill="#d4cbc3" />
          <ellipse cx={rightTragion.x + 1} cy={rightTragion.y + 14} rx="12" ry="31" fill="#d4cbc3" />
          <g filter="url(#verifiedFrontMeshShadow)">
            <CanonicalClayFace view="front" landmarks={landmarks} />
          </g>
        </g>''',
    '''        <g filter="url(#verifiedFrontMeshShadow)">
          <CanonicalClayFace view="front" landmarks={landmarks} />
        </g>''',
)

replace_once(
    ROOT / "verified_chunks/part4.tsx",
    '''        <g>
          <path d="M 112 620 C 170 574, 250 554, 303 548 C 363 552, 443 578, 510 620 Z" fill="#c6c0ba" />
          <g filter="url(#verifiedProfileMeshShadow)">
            <CanonicalClayFace view="profile" landmarks={landmarks} />
          </g>
        </g>''',
    '''        <g filter="url(#verifiedProfileMeshShadow)">
          <CanonicalClayFace view="profile" landmarks={landmarks} />
        </g>''',
)
