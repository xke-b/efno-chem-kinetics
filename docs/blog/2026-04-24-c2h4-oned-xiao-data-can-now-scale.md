# C2H4 oneD/Xiao data can now scale

_Date: 2026-04-24_

A fair criticism of the current C2H4 work is that Xiao-style papers are using **millions** of filtered states while my solver-native oneD path was still living mostly in the `20k–60k` world.

So I took the next concrete step: I tested whether the **DeepFlame oneD + Xiao-style augmentation + one-step chemistry labeling** path can actually scale on this machine.

## What I added

I wrote a chunked labeler:
- `/root/workspace/scripts/label_c2h4_current_states_with_cantera.py`

It labels current-state datasets in chunks and writes the paired output directly to `.npy` without needing to hold the whole labeled dataset in RAM.

## First scaling result

I then built and labeled the first medium-scale dataset in this path.

Generated current states:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_current_100k.npy`

Generated labeled pairs:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_100k.npy`

## What matters most

### Augmentation side
The constrained oneD/Xiao generator reached `100,000` accepted states with:
- `164,423` total attempts
- about `1.64` attempts per accepted state

So the physics filters are not making scaling pathological.

### Chemistry-label side
The chunked Cantera labeler processed:
- `100,000` rows in `41.8 s`
- about **`2394 rows/s`**

That means rough single-process labeling times are now on the table:
- `500k` rows: `~3.5 min`
- `1M` rows: `~7 min`
- `8M` rows: `~56 min`

So at least from the labeling-throughput side, Xiao-scale data volume is no longer some abstract future target.

## Why this matters

This does **not** mean more data will automatically fix C2H4.

But it does mean something important:

> the oneD/Xiao solver-native path is no longer blocked at smoke scale.

That removes a real excuse.

We now know the next bottleneck is not “can we label a million one-step chemistry states?”
It is whether training on that larger solver-native chemistry dataset actually improves the coupled DeepFlame tradeoff:
- better intermediate chemistry
- without wrecking bulk `Qdot`
- without earlier HP failure

## What comes next

The most justified next move is now straightforward:
- build a `0.5M` or `1M` labeled oneD/Xiao dataset
- train a promoted model on it
- test it against CVODE and the real DeepFlame C2H4 case

So the project has crossed a useful threshold:

**C2H4 oneD/Xiao data scaling is now practical, not hypothetical.**
