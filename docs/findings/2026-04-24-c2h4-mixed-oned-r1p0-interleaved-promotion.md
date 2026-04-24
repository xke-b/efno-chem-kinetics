# C2H4 larger mixed-data promotion (`dp100 + oneD@1.0`): scaling the oneD chemistry add-on to parity with the case-pair backbone does not improve the promoted interleaved-attention branch, and the deployed case still fails at the first learned step

_Date: 2026-04-24_

## Why this was the next step

After showing that:
- pure oneD/Xiao `100k` chemistry scaling does not rescue deployment, and
- the oneD path is likely more useful as an augmentation source than as a standalone training source,

the next sharp test was to return to the **mixed-data regime** and ask:

- what happens if the oneD DeepFlame Xiao-style chemistry add-on is no longer a small `0.2` supplement,
- but instead scaled up to parity with the `dp100` case-pair backbone?

This is the most direct first test of whether “more oneD chemistry support” helps **when attached to the stronger solver-aligned backbone** rather than used alone.

## New dataset assets

Random oneD labeled subset:
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_50k_seed0.npy`
- `/root/workspace/data/c2h4_oned_deepflame_interp_aug_labeled_50k_seed0.json`

Larger mixed dataset:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r1p0.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_oned_deepflame_r1p0.json`

Composition:
- `50000` rows from `dp100`
- `50000` rows from the oneD/Xiao labeled pool
- total: `100000`
- effective oneD add-on ratio relative to `dp100`: **`1.0`**

## Training setup

Tag:
- `c2h4_casepair_dp100_plus_oned_deepflame_r1p0_fno_powerdelta_attn1_interleaved_promoted100_val`

Checkpoint:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r1p0_fno_powerdelta_attn1_interleaved_promoted100_val.pt`

Bundle:
- `/root/workspace/artifacts/models/c2h4_casepair_dp100_plus_oned_deepflame_r1p0_fno_powerdelta_attn1_interleaved_promoted100_val_deepflame_bundle/`

Training summary:
- `/root/workspace/artifacts/experiments/c2h4_casepair_dp100_plus_oned_deepflame_r1p0_fno_powerdelta_attn1_interleaved_promoted100_val_baseline/summary.json`

Configuration:
- target: `species_power_delta`
- architecture: FNO + **interleaved attention**
- epochs budget: `100`
- GPU training
- validation fraction: `0.1`
- train / validation rows: `90000 / 10000`
- batch size: `1024`

Observed result:
- best epoch: `100`
- best validation loss: **`0.15577511340379716`**

## Offline comparison against earlier promoted branches

For context:
- mixed `dp100 + oneD@0.2` promoted power-delta best val loss: `0.13110`
- mixed `dp100 + oneD@0.2` promoted **interleaved-attention** best val loss: `0.11611`
- larger mixed `dp100 + oneD@1.0` promoted interleaved-attention best val loss: **`0.15578`**

So at least by this validation metric, scaling the oneD add-on from `0.2` to `1.0` made the promoted mixed-data branch **worse, not better**.

## DeepFlame deployment result

Case:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r1p0_fno_powerdelta_attn1_interleaved_promoted100_val_np8`

Logs:
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r1p0_fno_powerdelta_attn1_interleaved_promoted100_val_np8/run.log`
- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_casepair_dp100_plus_oned_deepflame_r1p0_fno_powerdelta_attn1_interleaved_promoted100_val_np8/solver.err`

Main result:
- the case writes `1e-07`
- the first learned step begins at `2e-07`
- the case then fails in HP reconstruction during thermodynamic correction

So the larger oneD-augmented mixed dataset still does **not** rescue early deployment stability.

## Failure signature

At `2e-07`, the run log shows:
- `real inference points number: 33508`
- learned GPU inference is active
- transport and species equations proceed
- then the case fails in `ThermoPhase::setState_HPorUV (HP)`

Representative failed state:
- target enthalpy `171659.31154943048`
- pressure `100717.23818534247`
- starting temperature `2145.5332204131223`

This is qualitatively similar to the other early C2H4 learned-model HP failures: the learned update is producing a thermodynamic state that the downstream HP reconstruction cannot recover robustly.

## Interpretation

This is another useful negative result.

### What it tells us

1. **More oneD chemistry support is not monotonically helpful even in the mixed regime.**
   - Going from `oneD@0.2` to `oneD@1.0` does not improve the promoted mixed branch.

2. **The better role for oneD/Xiao support is still unresolved quantitatively.**
   - Too little oneD support did not fix chemistry.
   - Much more oneD support now degrades validation fit and still fails early in deployment.

3. **The mixed-data problem is not just a simple scaling-ratio issue.**
   - This strengthens the idea that we likely need either:
     - more structured mixing,
     - regime-selective use of oneD data,
     - species-aware supervision,
     - or better deployment-side architecture/target handling.

4. **The interleaved-attention branch remains promising as an architecture family, but not yet under this heavier oneD mixing regime.**
   - Interleaved attention helped offline within the earlier `r=0.2` neighborhood.
   - It does not rescue a much larger oneD chemistry fraction by itself.

## Current takeaway

The larger mixed-data test narrows the conclusion further:

> the oneD/Xiao chemistry path is valuable, but simply increasing its weight inside the mixed dataset from `0.2` to `1.0` is not a deployment-positive fix for C2H4.

That means the next mixed-data steps should become **more structured**, not just larger by ratio.

## Most useful next step

The next justified move is now likely one of:
1. keep the stronger promoted architecture branch, but return to a **smaller oneD ratio neighborhood** and add **species-aware weighting**
2. build a **regime-selective** mixed dataset rather than a uniform oneD concatenation
3. test whether the promoted interleaved-attention branch is better on a chemistry-richer but still narrower mixed composition than `r=1.0`
