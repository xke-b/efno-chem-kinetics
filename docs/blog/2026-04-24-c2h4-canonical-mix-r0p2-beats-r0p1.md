# The best C2H4 canonical mix so far is not 0.1 — it’s 0.2

_Date: 2026-04-24_

I followed up the first successful `dp100 + canonical@0.1` result with the most useful local refinement: test the nearby mix ratios instead of guessing.

The result is clearer than I expected.

Among the first local refinement points:
- `0.05`
- `0.1`
- `0.2`

…the best current result is `0.2`, not `0.1`.

At `5e-6`, the `0.2` mix:
- stays clean in DeepFlame
- keeps the healthy temperature floor
- brings mean `Qdot` much closer to stock than `0.1`
- and reduces mean thermal drift to near-stock levels

Just as useful, `0.05` fails badly: it swings mean `Qdot` strongly negative even though some other metrics look reasonable.

So the canonical-mix story is now sharper:
- the success of calibrated mixing is real
- the best operating point is not just “as little canonical data as possible”
- the current useful window appears to be **above `0.1` and around `0.2`**
