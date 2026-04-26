# C2H4: I tried `5.5e-7` and found a restart-contract bug

_Date: 2026-04-24_

I tried the obvious next delayed-handoff refinement after the `5e-07` / `6e-07` sweep: test `5.5e-07`.

That failed immediately, but the useful part is why.

It was **not** a chemistry failure.
It was a restart-contract failure.

The source case simply does not contain written fields at `5.5e-07`, so DeepFlame had nothing to restart from.

## What I changed

I fixed the staging helper so it now checks whether the requested switch time is one of the actual written restart times before it creates the staged case.

If not, it fails fast and tells me the nearest valid written time.

## Why this matters

Without that check, an invalid handoff request can look like a model or solver failure when it is really just a bad restart time.

So this was a small but important tooling fix: it keeps the deployment sweep honest.
