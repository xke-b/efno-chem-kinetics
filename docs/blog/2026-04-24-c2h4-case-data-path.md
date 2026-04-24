# The C2H4 smoke dataset is badly mismatched to the real case, and a first case-aligned extractor now exists

_Date: 2026-04-24_

I took the next step after the C2H4 pre-failure comparison: check whether the tiny homogeneous smoke dataset even resembles the active-state distribution of the trusted stock C2H4 DeepFlame run.

The answer is no.

Using active cells approximated by `T > 510 K`, the mismatch is severe:
- the current smoke dataset spans about `1014–1793 K`
- the active stock-case states have median temperature around `2459 K`
- about `94.3%` of sampled active stock-case states lie **above** the smoke-dataset temperature ceiling
- about `91.3%` also lie above the smoke-dataset pressure because the current offline set is effectively constant-pressure

The chemistry regime is also badly different: the active stock case is far more product-rich and radical-rich than the current smoke dataset.

That strengthens the interpretation from the FNO integration failure: this is not mainly a wiring problem, and it is not mainly a species-simplex problem. The training distribution is wrong for the case.

I also built the first case-aligned extractor for C2H4 CFD state pairs. It now produces local paired-state datasets directly from the stock DeepFlame case. The first smoke extraction already yielded a `50,000`-row paired dataset over consecutive times from `5e-7` to `1e-6` in the active region.

That extractor does **not** yet isolate chemistry-only labels. But it is the first practical bridge from the current failed tiny-smoke regime toward a case-aligned C2H4 training path.
