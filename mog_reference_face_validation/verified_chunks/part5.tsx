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
  const front = useMemo(referenceFrontLandmarks, []);
  const profile = useMemo(referenceProfileLandmarks, []);
  const report = useMemo(() => calculateAnalysisReport(front, profile, "neutral"), [front, profile]);
  const metrics = report.metrics.filter((metric) => metric.view === view && metric.referenceBand);
  const allWithin = metrics.every((metric) => metric.fitStatus === "within");

  return (
    <section id="ideal-reference" className="mt-12 scroll-mt-24 border border-[var(--line)] bg-white">
      <div className="border-b border-[var(--line)] p-5 sm:p-7">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--accent)]">Verified reference geometry</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em]">One face that satisfies Mog’s own measurements</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--muted)]">Structure and realistic modes use the exact same solved landmarks. Realistic mode warps a licensed canonical facial mesh to those anchors and adds neutral clay shading; none of those illustrative details enters the harmony score.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Toggle value={view} options={["front", "profile"] as const} onChange={setView} label="Face view" />
            <Toggle value={mode} options={["structure", "rendered"] as const} onChange={setMode} label="Rendering mode" />
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)]">
        <div className="min-h-[560px] border-b border-[var(--line)] bg-[var(--paper)] p-4 sm:p-8 lg:border-b-0 lg:border-r">
          <div className="mx-auto max-w-[580px]">{view === "front" ? <FrontReference mode={mode} landmarks={front} /> : <ProfileReference mode={mode} landmarks={profile} />}</div>
        </div>
        <div className="p-5 sm:p-7">
          <div className={`border px-3 py-2 text-xs font-semibold ${allWithin ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-amber-200 bg-amber-50 text-amber-900"}`}>
            {allWithin ? `${metrics.length}/${metrics.length} scored measurements recompute inside their target bands.` : "This reference does not yet satisfy every displayed target."}
          </div>
          <h3 className="mt-5 font-semibold">Measurements used in this view</h3>
          <p className="mt-2 text-xs leading-5 text-[var(--muted)]">Each value is recomputed from the displayed landmarks. Metrics without a defensible comparison convention remain raw measurements and are not presented as ideal targets.</p>
          <dl className="mt-5 max-h-[560px] divide-y divide-[var(--line)] overflow-y-auto border-y border-[var(--line)] pr-2">
            {metrics.map((metric) => (
              <div key={metric.id} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1 py-2.5 text-sm">
                <dt className="text-[var(--muted)]">{metric.shortName}</dt>
                <dd className="font-mono text-xs font-semibold tabular-nums">{metric.formattedValue}</dd>
                <dd className="col-span-2 text-[11px] text-[var(--muted)]">Target {metric.referenceBand!.low}–{metric.referenceBand!.high}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-5 text-xs leading-5 text-[var(--muted)]">This is one mathematically valid neutral solution, not the only attractive face and not a claim that one universal perfect face exists.</p>
        </div>
      </div>
    </section>
  );
}
