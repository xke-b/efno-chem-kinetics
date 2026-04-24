# A cleaner-looking C2H4 training subset can still be worse in the real solver

_Date: 2026-04-24_

I tried the next obvious mixed-filter refinement for C2H4 case-pair labels:
- `|Δp| <= 100 Pa`
- `|ΔT| <= 10 K`

Offline, it looked great. The training loss dropped much lower than in the earlier pressure-only filtered runs.

But in the real DeepFlame case, it was worse.

The mixed-filter model failed around `4.2e-6` with an HP reconstruction error, and the active learned set had already started shrinking rather than growing. The pre-failure log also showed the cold-tail pathology returning.

That is a very useful failure.

It means a dataset can look cleaner and easier to fit offline while becoming less useful for the coupled solver, because it no longer covers enough of the broader transitions the runtime still visits.

So the lesson from this ablation is sharp: do not overtrust smaller-step filtering just because the offline loss gets better. For this deployment-facing problem, the broader dp100 subset is still the best current filter in the family.
