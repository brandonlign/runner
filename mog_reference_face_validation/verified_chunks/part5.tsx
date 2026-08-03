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
