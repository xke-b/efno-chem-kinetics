# Corrected-decode EFNO vs supervised MLP: after fixing the decode contract, self-rollout EFNO becomes decisively better than supervised on H2 rollout metrics

_Date: 2026-04-23_

## Why this was the next step

Once the BCT-state decode fix was identified, the old EFNO-vs-supervised comparison was no longer the right benchmark.

The next necessary step was to re-anchor the program against the seeded supervised MLP reference already used earlier in the day.

## Inputs compared

Supervised reference:
- `/root/workspace/artifacts/experiments/h2_temp_species_seeded_replicates/summary.json`
- case: `supervised_deltaT_25ep`

Corrected-decode EFNO summary:
- `/root/workspace/artifacts/experiments/h2_efno_bct_state_decode_ablation/summary.json`

Comparison artifact:
- `/root/workspace/artifacts/experiments/h2_corrected_decode_vs_supervised_comparison/summary.json`

Compared corrected-decode EFNO cases:
1. `teacherforced_rollout0p1_bctdecode`
2. `self_rollout0p1_bctdecode`
3. `self_rollout0p1_predicted_main_bct_bctdecode`

## Supervised seeded reference
- one-step species MAE: `6.228e-05`
- one-step temperature MAE: `1.752e-01 K`
- one-step element-mass MAE: `1.231e-04`
- rollout species MAE @1000: `2.779e-01`
- rollout temperature MAE @1000: `1.494e+03 K`
- rollout element-mass MAE @1000: `6.294e-01`

## Corrected-decode EFNO results

### Corrected teacher-forced EFNO
- one-step species MAE: `8.253e-05`
- one-step temperature MAE: `1.210e-01 K`
- one-step element-mass MAE: `1.556e-04`
- rollout species MAE @1000: `2.972e-02`
- rollout temperature MAE @1000: `7.047e+02 K`
- rollout element-mass MAE @1000: `5.777e-02`

Relative to supervised:
- one-step species MAE: `1.33x` worse
- one-step temperature MAE: `0.69x` of supervised
- one-step element MAE: `1.26x` worse
- rollout species MAE: `0.107x` of supervised
- rollout temperature MAE: `0.472x` of supervised
- rollout element MAE: `0.092x` of supervised

### Corrected self-rollout EFNO
- one-step species MAE: `1.023e-04`
- one-step temperature MAE: `1.240e-01 K`
- one-step element-mass MAE: `1.980e-04`
- rollout species MAE @1000: `1.017e-02`
- rollout temperature MAE @1000: `9.598e+01 K`
- rollout element-mass MAE @1000: `1.034e-02`

Relative to supervised:
- one-step species MAE: `1.64x` worse
- one-step temperature MAE: `0.71x` of supervised
- one-step element MAE: `1.61x` worse
- rollout species MAE: `0.0366x` of supervised
- rollout temperature MAE: `0.0642x` of supervised
- rollout element MAE: `0.0164x` of supervised

### Corrected self-rollout EFNO + predicted-main-BCT
- one-step species MAE: `9.903e-05`
- one-step temperature MAE: `1.235e-01 K`
- one-step element-mass MAE: `1.894e-04`
- rollout species MAE @1000: `7.715e-03`
- rollout temperature MAE @1000: `7.352e+01 K`
- rollout element-mass MAE @1000: `6.237e-03`

Relative to supervised:
- one-step species MAE: `1.59x` worse
- one-step temperature MAE: `0.705x` of supervised
- one-step element MAE: `1.54x` worse
- rollout species MAE: `0.0278x` of supervised
- rollout temperature MAE: `0.0492x` of supervised
- rollout element MAE: `0.00991x` of supervised

## Main interpretation

### 1. The corrected-decode EFNO family is now clearly superior to supervised for rollout use
All corrected-decode EFNO variants beat the seeded supervised MLP reference decisively on the key long-horizon rollout metrics.

The strongest current branch, corrected self-rollout + predicted-main-BCT, reduces the supervised reference by about:
- `36x` on rollout species MAE @1000
- `20x` on rollout temperature MAE @1000
- `101x` on rollout element-mass MAE @1000

### 2. The remaining EFNO cost is now concentrated in one-step species fidelity
The corrected EFNO branches still trail supervised on:
- one-step species MAE
- one-step element-mass MAE

But they are already better on one-step temperature MAE, and they are vastly better on the rollout metrics that matter for coupled simulation usefulness.

### 3. The benchmark conclusion changed materially after the decode fix
Before the fix, supervised was the cleanest overall reference and teacher forcing looked necessary for strong EFNO rollout behavior.

After the fix:
- self-rollout is no longer pathological
- corrected self-rollout is stronger than corrected teacher forcing on rollout
- corrected EFNO is now clearly ahead of supervised for the H2 offline rollout benchmark

## Bottom line

The decode fix did not just rescue a broken branch.
It changed the offline leaderboard.

The best current H2 EFNO branch is now:
- **corrected self-rollout + predicted-main-BCT**

and it is decisively stronger than the seeded supervised MLP reference on the rollout metrics most relevant to downstream coupled use.
