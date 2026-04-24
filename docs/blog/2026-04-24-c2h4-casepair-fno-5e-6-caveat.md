# The case-aligned C2H4 FNO reaches `5e-6`, but late-time trust is not solved yet

_Date: 2026-04-24_

I pushed the first case-aligned C2H4 FNO farther.

Good news first:
- it reaches `2e-6` cleanly
- then continues all the way to `5e-6`
- this is a major improvement over the earlier homogeneous-smoke FNO, which failed during the `1e-6` attempt

That is strong evidence that training-distribution alignment matters a lot for this problem.

But there is an important caveat.

At the `5e-6` step, the log reports a Python-side:
- `CUDA error: out of memory`

and the written `Qdot` field for the case-aligned FNO run is all zeros at `5e-6`.

So the late run is not yet fully trustworthy as scientific evidence of a healthy learned replacement. The short-horizon thermodynamic collapse seems fixed, but a new late runtime/inference issue appears once the active learned set grows large.

That means the current result is simultaneously:
- a real milestone for the data-path hypothesis
- and a clear warning not to overclaim success at `5e-6` yet

The next step is now sharper: diagnose and fix the late GPU-memory/inference-path failure mode in the case-local FNO bridge.
