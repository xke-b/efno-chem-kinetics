# A more chemistry-like C2H4 target subset now exists: pressure-filtered case pairs

_Date: 2026-04-24_

The next bottleneck after fixing the C2H4 runtime path is target quality. The full case-pair labels are useful, but they still mix chemistry with the rest of the CFD step.

So I looked for a cheap next refinement: a near-constant-pressure active subset of the case-pair data.

Across active pairs from `5e-7` to `1e-6` in the trusted stock run:
- median `|Δp|` is about `49 Pa`
- about `62.3%` of active pairs satisfy `|Δp| <= 100 Pa`
- about `96.1%` satisfy `|Δp| <= 250 Pa`

That means there is a substantial active subset with relatively small pressure drift.

I updated the C2H4 case-pair extractor to support pressure filters and generated a first filtered dataset with:
- `T > 510 K`
- `|Δp| <= 100 Pa`

The result is a new `50,000`-row filtered paired-state dataset that should be a bit more chemistry-like than the unfiltered CFD pair labels, while still being easy to generate reproducibly.

This does not make the labels chemistry-only. But it gives the project a better next baseline to try before a more ambitious labeling path.
