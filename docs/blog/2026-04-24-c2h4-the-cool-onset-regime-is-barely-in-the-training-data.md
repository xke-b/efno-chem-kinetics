# C2H4: the cool-onset regime is barely in the training data

_Date: 2026-04-24_

I followed up the CFD-state-vs-CVODE diagnosis with a simpler but very important question:

When the real C2H4 CFD case enters the `510–700 K` onset regime, do the offline training datasets actually contain nearby labeled examples with similar chemistry?

Right now, the answer looks like **not really**.

## What I checked

I took the real active CFD cells from the stock C2H4 case at `1e-07`, split them into:
- a **cool onset** benchmark: `510–700 K`
- a **hot active** benchmark: `1600–2600 K`

Then for each benchmark state I:
- computed the true one-step chemistry change with Cantera/CVODE
- found the nearest current-state neighbors in the offline datasets
- compared the neighbor labels with the real one-step chemistry from that CFD state

## What stood out most

### 1) The onset regime is only a tiny slice of the current datasets
Across the current datasets, only about **3–4%** of rows live in `510–700 K`.

That is already bad news for a regime that now looks central to the coupled failures.

### 2) The nearest neighbors for cool CFD states are often not cool at all
For the real cool CFD cells, the nearest offline neighbors are often around **2400 K**.

That means the onset-regime CFD states are not finding truly local support in the current offline manifold.

### 3) The neighbor labels are almost chemistry-dead compared with CVODE
For the cool-onset benchmark, the true one-step chemistry is strong.
But the nearest offline labels are almost zero.

That is true for:
- the case-pair backbone
- the mixed datasets
- even the current oneD/Xiao chemistry dataset

So the model is being asked to learn onset chemistry from local examples that mostly do **not** look like real onset chemistry.

## Why this matters

This is probably the clearest evidence so far that the C2H4 bottleneck is a **training-data support problem**, not just a model-capacity problem.

It also helps explain why the interleaved-attention branches tend to shut chemistry off in the cool onset regime: the local labels available to them are weak or mismatched there.

## What this points to next

The next useful step is not another blind ratio sweep.
It is more likely one of these:
- targeted data construction for real **cool-onset CFD-like states**
- chemistry-native relabeling for that regime
- species-aware supervision focused on onset intermediates

So this was a good failure-analysis step: it tells us the issue is not only that the model is wrong, but that the training data are giving it very little local support for the regime that seems to matter most.
