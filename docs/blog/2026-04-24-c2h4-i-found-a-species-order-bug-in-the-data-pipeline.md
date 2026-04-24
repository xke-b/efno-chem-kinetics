# C2H4: I found a species-order bug in the data pipeline

_Date: 2026-04-24_

While trying to build targeted cool-onset support data for C2H4, I found a more basic problem:

- the CFD case-pair datasets use one species order
- the Wu24sp / Cantera mechanism uses another
- the oneD/Xiao chemistry-labeled datasets were following the mechanism order
- but the mixed datasets were being concatenated without reordering

So some of the mixed C2H4 datasets were literally combining rows with **different channel meanings in the same columns**.

That was bad enough. But there was a second consequence too: some of my newer CFD-state-vs-CVODE analyses were feeding case-order CFD states into Cantera as if they were already in mechanism order.

## What changed after fixing it

The biggest correction was in the `510–700 K` cool-onset CFD states at `1e-07`.

Before the fix, the one-step chemistry looked strong.
After the fix, it is much smaller.

For those real cool-onset CFD cells:
- wrong species-order interpretation gave mean total `ΔY` activity of about **`0.328`**
- corrected interpretation gives about **`1.13e-4`**

So the earlier story that these cells were undergoing very strong onset chemistry at `1e-07` was overstated by the order bug.

## What still seems true

The correction does **not** make every C2H4 issue disappear.

The plain promoted power-delta branch still looks bad under corrected analysis:
- it still strongly overreacts in the hot regime
- its `OH` response is still wildly too large

But the interleaved-attention branch now looks much less obviously wrong at the early `1e-07` slice than I previously thought.

## What I fixed in the tooling

I updated the pipeline so that:
- mixed paired datasets are reordered into a common species layout before concatenation
- the current-state Cantera labeler can read input species order from metadata
- the newer C2H4 CFD-state analysis scripts reorder case states into mechanism order before computing Cantera references

I also built:
- a corrected aligned mixed `r=0.2` dataset
- a corrected cool-onset CFD chemistry support dataset

## What this means for the research thread

This is annoying, but it is also useful.

It means the project now has a clearer confounder identified:
- some mixed-data conclusions were contaminated by a **species-order alignment bug**
- some early cool-onset chemistry conclusions were contaminated too

So the next step is to rerun the important C2H4 comparisons in the corrected order-aligned regime, especially closer to the **later pre-failure window** where the coupled simulation actually breaks.

This is a real setback for some interpretations, but it is also real progress because now the pipeline is more trustworthy than it was this morning.
