            <line x1={g.pronasale.x} y1={g.pronasale.y} x2={g.pogonion.x} y2={g.pogonion.y} />
            <line x1={g.subnasale.x} y1={g.subnasale.y} x2={g.pogonion.x} y2={g.pogonion.y} />
            <line x1={g.gonion.x} y1={g.gonion.y} x2={g.menton.x} y2={g.menton.y} />
            <line x1={g.gonion.x} y1={g.gonion.y} x2={g.ramus.x} y2={g.ramus.y} />
          </g>

          {points.map(([name, point]) => (
            <circle key={name} cx={point.x} cy={point.y} r="4" fill="white" stroke="var(--accent)" strokeWidth="2"><title>{name}</title></circle>
          ))}
          <g fill="var(--muted)" fontSize="11">
            <text x={g.tragion.x - 6} y={g.tragion.y - 11}>Frankfort plane</text>
            <text x={g.pronasale.x + 10} y={g.pronasale.y - 5}>tip</text>
            <text x={g.pogonion.x + 10} y={g.pogonion.y}>pogonion</text>
            <text x={g.gonion.x - 58} y={g.gonion.y - 9}>gonion</text>
          </g>
        </g>
      )}
    </svg>
  );
}

function Toggle<T extends string>({ value, options, onChange, label }: { value: T; options: readonly T[]; onChange: (value: T) => void; label: string }) {
  return (
    <div className="flex border border-[var(--line)] bg-white p-1" role="group" aria-label={label}>
      {options.map((option) => (
        <button key={option} type="button" onClick={() => onChange(option)} aria-pressed={value === option} className={`px-3 py-2 text-sm capitalize transition-colors ${value === option ? "bg-[var(--ink)] text-white" : "text-[var(--muted)] hover:text-[var(--ink)]"}`}>
          {option === "rendered" ? "Realistic" : option === "profile" ? "Side" : option}
        </button>
      ))}
    </div>
  );
}

export function IdealReferenceFace() {
  const [view, setView] = useState<FaceView>("front");
  const [mode, setMode] = useState<RenderMode>("structure");
  const targets = view === "front" ? FRONT_TARGETS : PROFILE_TARGETS;

  return (
    <section id="ideal-reference" className="mt-12 scroll-mt-24 border border-[var(--line)] bg-white">
      <div className="border-b border-[var(--line)] p-5 sm:p-7">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--accent)]">Current harmony target</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">The face implied by Mog’s measurements</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--muted)]">Both modes use the same ratio-derived anatomical framework. Structure exposes scored landmarks and guides; realistic mode renders that framework as a restrained natural illustration. Color and shading are illustrative only and never enter the score.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Toggle value={view} options={["front", "profile"] as const} onChange={setView} label="Face view" />
            <Toggle value={mode} options={["structure", "rendered"] as const} onChange={setMode} label="Rendering mode" />
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-[minmax(0,1.35fr)_minmax(250px,0.65fr)]">
        <div className="min-h-[520px] border-b border-[var(--line)] bg-[var(--paper)] p-4 sm:p-8 lg:border-b-0 lg:border-r">
          <div className="mx-auto max-w-[560px]">{view === "front" ? <FrontFace mode={mode} /> : <ProfileFace mode={mode} />}</div>
        </div>
        <div className="p-5 sm:p-7">
          <h3 className="font-semibold">Target centers used in this view</h3>
          <p className="mt-2 text-xs leading-5 text-[var(--muted)]">Values come directly from Mog’s current neutral reference bands. The face shape uses scored geometry; visual styling remains separate.</p>
          <dl className="mt-5 divide-y divide-[var(--line)] border-y border-[var(--line)]">
            {targets.map((metric) => (
              <div key={metric.id} className="flex items-baseline justify-between gap-4 py-2.5 text-sm">
                <dt className="text-[var(--muted)]">{metric.label}</dt>
                <dd className="font-mono text-xs font-semibold tabular-nums">{targetLabel(metric)}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-5 text-xs leading-5 text-[var(--muted)]">Some measurements are dependent or internally inconsistent. The display preserves coherent human anatomy while minimizing disagreement with the current targets; it does not add extra scoring inputs.</p>
        </div>
      </div>
    </section>
  );
}
