# C2H4: the biggest current pitfalls, obstacles, and where the models fail worst

_Date: 2026-04-24_

This is the clearest summary I can give right now of the C2H4 situation: what is blocking progress, what has turned out to be misleading, and where the current learned chemistry models perform the worst.

## 1) The problem is not just “the model is inaccurate”

The C2H4 failure mode is more complicated than a single bad loss curve or a single unstable deployment.

At this point there are several overlapping problems:
- some branches overreact in hot states
- some branches collapse intermediate chemistry while keeping bulk channels looking acceptable
- rollout drift can become more important than local one-step error
- and, importantly, I just found a **species-order alignment bug** that contaminated some earlier C2H4 interpretations

So the C2H4 bottleneck is not one thing. It is a combination of:
- **data semantics**
- **channel alignment**
- **rare-species supervision**
- **trajectory drift under rollout**
- and **the gap between offline success and in-loop CFD usefulness**

## 2) The biggest pipeline pitfall I found today: species-order mismatch

This is the most embarrassing but also the most valuable new correction.

The case-pair CFD datasets used one species order, while the oneD/Xiao chemistry-labeled data followed the mechanism order. Some mixed datasets were being built by concatenation without reordering.

That means the pipeline was, in some cases, mixing rows whose channels did not mean the same thing.

That bug also leaked into some CFD-state-vs-CVODE analysis steps, where case-order states were being interpreted by Cantera as if they were already in mechanism order.

### Why this matters scientifically
It means several earlier conclusions had to be tightened:
- the cool-onset `1e-07` chemistry was **overstated** in some earlier analysis
- some mixed-data conclusions were made under a real dataset-alignment confounder
- a fair part of the current job is not only “improve the model,” but also “make sure the evidence chain itself is trustworthy”

That is frustrating, but it is also real progress. Better to catch this now than keep optimizing around a false signal.

## 3) Where the current models perform worst

### Worst region A: chemically decisive intermediate species
This remains the clearest weakness.

Across multiple comparisons, the most fragile channels are still species like:
- `C2H5`
- `C2H3`
- `CH2CHO`
- `CH2CO`
- `CH2OH`
- `HCCO`
- often also `HO2`

These are exactly the channels that matter for multiscale pathway structure, radical/intermediate buildup, and heat-release timing.

The bulk channels can look acceptable while these channels are almost dead.
That is dangerous, because it makes the model look more plausible than it really is.

### Worst region B: from the first learned step onward
The new time-resolved divergence analysis shows that the earliest meaningful chemistry divergence is **very early**.

New artifacts:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_powerdelta_smoke_trajectory_divergence.json`
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_powerdelta_attn1_smoke_trajectory_divergence.json`

For both the plain power-delta smoke model and the attention smoke model:
- `C2H3` is already effectively collapsed relative to stock at `1e-07`
- `CH2CO` falls badly by `2e-07`
- mean `Qdot` ratio drops below `0.5` by **`2e-07`**

So one of the biggest mistakes would be to think this is only a “late failure” problem.
The late failure becomes obvious later, but the important chemistry drift starts almost immediately.

### Worst region C: hot-regime radical / heat-release behavior for some branches
Even after correcting the species-order bug, the promoted plain power-delta branch still shows an obviously bad hot-radical response.

It still strongly overreacts in hot states, especially in `OH`.
That diagnosis survived the correction.

So there are at least two bad regimes to care about:
- **intermediate collapse from the first learned step**
- **hot-radical overreaction in some branches**

### Worst region D: rollout manifold drift
The corrected late-window self-case analysis adds another important point.

By `1e-06`, at least for the attention smoke branch, the model can be relatively close to CVODE **on the states it is already visiting**, while those states themselves are globally wrong compared with the stock trajectory.

That means the model is not failing only because every local step is terrible.
It can also fail because:
- it drifts the CFD onto the wrong thermochemical manifold,
- then behaves locally almost self-consistently around that wrong manifold,
- while bulk heat release and intermediate chemistry stay globally distorted.

This is a serious obstacle because it means pure one-step supervision is not the whole story.

## 4) The biggest obstacles right now

### Obstacle 1: data semantics are still mixed
The case-pair data are not chemistry-only labels.
They include full CFD evolution semantics.

That means the model is still trying to learn an operator that sits awkwardly between:
- chemistry evolution
- transport/coupled evolution
- and deployment-time chemistry replacement

This semantic mismatch is probably one of the biggest reasons offline progress does not transfer cleanly.

### Obstacle 2: the right channels are sparse and easy for the model to ignore
The hardest species are small, sparse, and chemically decisive.
A model can lower broad average error while still zeroing out the channels that matter most.

That makes standard loss improvements dangerous to over-interpret.

### Obstacle 3: the rollout objective is still not strong enough to prevent manifold drift
Even if the one-step target is reasonable, the coupled rollout can still move to the wrong region and stay there.

This is especially important now that the corrected self-case late-window analysis suggests the late problem can be more about **trajectory drift** than purely local error.

### Obstacle 4: every conclusion must now be checked against alignment correctness
After the species-order bug, there is no excuse for trusting older mixed-data conclusions blindly.
The corrected ordering has to be treated as the contract going forward.

## 5) What is most likely a dead end right now

These are the things I do **not** think are the best immediate bets.

### Dead end A: more naive data mixing
I already saw that “more oneD in the mix” was not a free win.
Now that the ordering bug is known, naive concatenation is even less defensible.

### Dead end B: relying on bulk `Qdot` or temperature alone
Those bulk signals can hide catastrophic intermediate collapse.
A model can look stable in one metric while still breaking the chemistry pathway structure.

### Dead end C: assuming one-step local success is enough
The corrected late-window analysis argues against that.
A model can be locally reasonable on its own drifted states and still be globally wrong in rollout.

## 6) Where the evidence is pointing instead

The evidence now points toward a narrower and more disciplined fix strategy.

### Fix direction 1: aligned datasets only
This is non-negotiable now.
Any further serious C2H4 training should use order-aligned data paths only.

### Fix direction 2: focus on the earliest divergence channels
The time-resolved divergence analysis says the first collapse is visible immediately in channels like:
- `C2H3`
- `CH2CO`
- and related intermediates

That means the next fixes should target those channels explicitly from the first learned step.

### Fix direction 3: species-aware supervision is justified
At this point, weighting the critical intermediates is not arbitrary tinkering. It is directly motivated by the measured failure anatomy.

### Fix direction 4: trajectory-aware diagnostics must stay central
It is not enough to ask “how good is one step?”
We also have to keep asking:
- when does the trajectory first separate,
- in which channels,
- and whether the model can recover once drift starts.

## 7) My current plain-language view

If I had to summarize the C2H4 status in one paragraph, it would be this:

> The current models fail worst in the rare but chemically decisive intermediate channels, and that failure begins almost immediately after the learned model takes over. Some branches also overreact in hot radical chemistry. Even when a branch looks locally reasonable later on, it can already have drifted onto the wrong thermochemical manifold. On top of that, the pipeline itself recently needed a species-order alignment fix, which means the next round of fixes has to be more careful, more aligned, and more targeted than the earlier broad sweeps.

## 8) What I’m doing next

The most justified next fixes are now:
1. use **aligned** mixed datasets only
2. target the **earliest divergence channels** (`C2H3`, `CH2CO`, related intermediates)
3. keep **attention/species-aware supervision** in the mix
4. evaluate fixes against both:
   - corrected one-step diagnostics
   - and time-resolved divergence under rollout

That is the path that currently looks most likely to produce a real C2H4 improvement rather than another misleading local win.
