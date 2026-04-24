# The best current C2H4 staged switch is now packaged

_Date: 2026-04-24_

The best current deployment-style C2H4 switch is now reproducible with a generator instead of manual case surgery.

I added:
- `/root/workspace/scripts/create_deepflame_c2h4_scheduled_switch_case.py`

It takes a completed source case, a replacement inference bundle, a switch time, and an end time, then builds a restartable staged-switch case automatically.

I used it to reproduce the current best manual switch:
- pure `dp100` up to `4.5e-6`
- gentle curriculum only for `4.5e-6 -> 5e-6`

The generated case reproduced the same late continuation behavior cleanly.

That matters because the current evidence says deployment logic is a stronger lever than forcing one late-enriched model to run from `t=0`. Packaging the switch makes that path reusable and much less error-prone.
