# Predictive-evidence external-control amendment

The first runner execution (`30844294688`) completed all null and injection calculations in memory but stopped before writing results because the untouched M2026-A1 window contained only 67 usable GMN events in 2019, below the protocol's 90-per-year sampling requirement.

This is a data-availability correction, not a result-driven statistical change. Before any Stage-0 result was inspected or preserved, the following amendment was frozen:

- null scenes remain at 90 sampled events per year;
- all injection scenes remain at 90 sampled events per year;
- all candidate-search rules, year orderings, e-value formulas, threshold `E >= 10`, and continuation gates remain unchanged;
- only the external M2026-A1 control uses 60 sampled events per year, which is below the observed 2019 availability of 67;
- the external control remains excluded from method design, null assessment, and injection comparisons.

A separate correction wrapper implements only this external-control sample size. The original failed execution is retained as an implementation audit trail and is not scientific evidence.
