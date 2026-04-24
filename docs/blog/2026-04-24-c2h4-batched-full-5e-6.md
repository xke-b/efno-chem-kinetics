# The full batched C2H4 case-aligned FNO run now reaches `5e-6` cleanly

_Date: 2026-04-24_

After fixing the case-local FNO bridge to run active cells in batches, I re-ran the **full** case-aligned C2H4 FNO trajectory from the start, not just the repaired final-step replay.

Result:
- the full run reaches `5e-6`
- no CUDA OOM line appears in the log
- the learned active-set count keeps growing through the horizon
- the written `Qdot` field remains nonzero at `5e-6`

This is the important upgrade over the earlier unbatched result. The previous late-time trust problem was real, but it was not only about the learned model. The bridge implementation itself was part of the failure.

With batching in place, the runtime path is now much more trustworthy:
- start-to-`5e-6` survives
- no late GPU OOM symptom
- no zero-`Qdot` collapse

That does not mean the learned chemistry is now perfect. The next question is more specific: how close is this full batched case-aligned FNO run to the stock C2H4 baseline in its actual thermochemical behavior?
