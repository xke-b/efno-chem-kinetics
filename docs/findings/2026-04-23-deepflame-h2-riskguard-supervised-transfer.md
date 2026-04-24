# DeepFlame H2 risk-guard transfer test: the FT650 logistic risk guard does not rescue the Burke supervised branch, which still collapses to full fallback by `1.2e-05`

_Date: 2026-04-23_

## Why this was the next step

After packaging the FT650 logistic risk-guard recipe, the next useful question was whether it transfers beyond the corrected Burke branch.

The most direct transfer target was the Burke supervised branch.

## Cases

Generated / prepared cases:
- plain supervised FT650:
  - `/root/workspace/runs/deepflame_h2_smoke/burke_supervised_mlp_ft650`
- supervised FT650 + logistic risk guard @ `0.5`:
  - `/root/workspace/runs/deepflame_h2_smoke/burke_supervised_mlp_ft650_riskguard`

For comparison:
- corrected FT650:
  - `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650`
- corrected FT650 + logistic risk guard @ `0.5`:
  - `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard`

## Artifact

- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_supervised_ft650_riskguard_transfer_comparison.json`

## Main result

The current FT650 logistic risk-guard recipe is **not** broadly transferable in a useful way to the Burke supervised branch.

It improves the supervised branch somewhat before the collapse, but it does **not** preserve learned participation long-term. The supervised branch still goes to full fallback by `1.2e-05`.

That means the current risk model is not a generic Burke-H2 deployment fix; it appears much more aligned with the corrected branch’s state/update regime.

## Supervised FT650 behavior

### Plain supervised FT650
- first time above `50%` fallback: `1.1e-05`
- first time above `80%` fallback: `1.2e-05`
- first time above `95%` fallback: `1.2e-05`
- learned fraction at `1e-05`: `0.7173`
- learned fraction at `1.4e-05`: `0.0`
- learned fraction at `2e-05`: `0.0`
- HP-failure fraction at `2e-05`: `1.0`

So the supervised branch is already much more fragile than the corrected branch even under the same `650 K` activation threshold.

### Supervised FT650 + risk guard
- first time above `50%` fallback: `1.2e-05`
- first time above `80%` fallback: `1.2e-05`
- first time above `95%` fallback: `1.2e-05`
- learned fraction at `1e-05`: `0.8803`
- learned fraction at `1.4e-05`: `0.0`
- learned fraction at `2e-05`: `0.0`
- HP-failure fraction at `2e-05`: `0.6553`
- cumulative fallback fraction at `2e-05`: `0.5631`

So the transfer does help in a limited sense:
- better learned fraction at `1e-05`
- lower cumulative fallback fraction than plain supervised FT650
- lower end-time HP-failure fraction than plain supervised FT650

But the central practical outcome does **not** change:
- the learned branch is gone by `1.2e-05`
- and remains gone thereafter

## Comparison to corrected branch

Corrected FT650:
- learned fraction at `2e-05`: `0.2944`

Corrected FT650 + risk guard:
- learned fraction at `2e-05`: `0.2411`
- HP-failure fraction at `2e-05`: `0.0223`

Supervised FT650:
- learned fraction at `2e-05`: `0.0`

Supervised FT650 + risk guard:
- learned fraction at `2e-05`: `0.0`
- HP-failure fraction at `2e-05`: `0.6553`

This contrast is strong evidence that the corrected branch is living in a materially different deployment regime than supervised. The same risk-guard mechanism that produces a plausible safety/retention tradeoff for corrected is nowhere near enough for supervised.

## Interpretation

This is a useful negative result.

It says the current logistic risk-guard recipe is:
- **not branch-agnostic**
- **not enough to rehabilitate a much weaker deployment branch**

In other words:
- the guard can shape the tradeoff within a viable branch
- but it does not turn a poor branch into a good one

That is scientifically useful because it strengthens confidence that the corrected branch really is the only serious H2 deployment candidate in the current program.

## Updated conclusion

The project now has a clearer deployment-facing recommendation:

- **Corrected FT650** remains the retention-oriented default.
- **Corrected FT650 + logistic risk guard @ `0.5`** remains the best current safety-oriented guarded prototype.
- The supervised branch should **not** be promoted as a competing guarded deployment candidate on the basis of the current transfer test.

## Most useful next step

The next valuable step should likely stay focused on the corrected branch, not the supervised branch.

The best options now are:
1. make the corrected FT650 plain / corrected FT650 risk-guard modes the documented default H2 deployment pair
2. package the risk model coefficients and guard selection more cleanly for reuse
3. if we want more scientific leverage, move to the next chemistry/case setting rather than spending more on supervised-branch rescue

This transfer test usefully narrows the forward path instead of widening it.
