# DeepFlame H2 FT650 state-conditioned failure map: the remaining late-time HP failures are concentrated in moderate-O2, mid-temperature, lower-H2O active states rather than a tiny extreme-O2 corner

_Date: 2026-04-23_

## Why this was the next step

The first `650 K + O2` guard helped for part of the run but still failed by `2e-05`.

That made the next useful step a data-driven failure map rather than more intuition-only guard tweaking.

## New script

- `/root/workspace/scripts/analyze_deepflame_h2_state_conditioned_hp_failure.py`

It:
1. reads written processor fields for selected times
2. extracts the DNN-active subset (`T > frozenTemperature`)
3. applies the exported DeepFlame-compatible species update
4. attempts HP reconstruction cell-by-cell
5. bins HP failures by current-state variables

Current bins:
- temperature
- `O2`
- `H2O`

## Artifacts

- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_state_conditioned_hp_failure.json`
- `/root/workspace/artifacts/experiments/deepflame_h2_smoke_analysis/burke_corrected_self_rollout_predmainbct_ft650_state_conditioned_hp_failure_summary.json`

Times analyzed:
- `1.2e-05`
- `1.6e-05`
- `2e-05`

## Main result

The late failure region is broader and more structured than “very high O2 near threshold.”

That explains why the first simple O2 guard was only partially successful.

## Time = `1.2e-05`
Overall active HP failure fraction:
- `0.0434`

Most dangerous current-state regions:
- temperature:
  - `[1000, 1200) K`: `0.1897`
  - `[1200, 1600) K`: `0.1441`
  - `[650, 800) K`: `0.1176`
- `O2`:
  - `[0.05, 0.10)`: `0.1804`
  - `[0.10, 0.15)`: `0.1140`
- `H2O`:
  - `[0.05, 0.10)`: `0.1327`
  - `[0.10, 0.15)`: `0.1032`

Interpretation:
- at this earlier stage, the risky cells are not the hottest cells
- they are more concentrated in moderate-temperature active states with moderate-to-high oxidizer and lower water content

## Time = `1.6e-05`
Overall active HP failure fraction:
- `0.2485`

Most dangerous current-state regions:
- temperature:
  - `[1200, 1600) K`: `0.7391`
  - `[650, 800) K`: `0.7379`
  - `[800, 1000) K`: `0.7083`
  - `[1000, 1200) K`: `0.6635`
- `O2`:
  - `[0.20, inf)`: `0.9231` (small count)
  - `[0.10, 0.15)`: `0.7923`
  - `[0.05, 0.10)`: `0.7807`
- `H2O`:
  - `[0.02, 0.05)`: `0.8443`
  - `[0.10, 0.15)`: `0.7826`
  - `[0.05, 0.10)`: `0.7551`

Interpretation:
- by the mid-late horizon, the failure region has expanded dramatically
- it is strongest in **moderate temperature** active cells, not mainly the very hottest cells
- it also tracks **moderate/high O2 with relatively low H2O**, i.e. less product-rich states

## Time = `2e-05`
Overall active HP failure fraction:
- `0.4790`

Most dangerous current-state regions:
- temperature:
  - `[1600, 2000) K`: `0.7012`
  - `[1200, 1600) K`: `0.6298`
  - `[650, 800) K`: `0.5288`
- `O2`:
  - `[0.02, 0.05)`: `0.5987`
  - `[0.05, 0.10)`: `0.5705`
  - `[0.20, inf)`: `0.5846` but low count
- `H2O`:
  - `[0.15, 0.20)`: `0.6951`
  - `[0.02, 0.05)`: `0.5474`

Interpretation:
- by the late horizon, the bad region is no longer a tiny corner
- it covers a broad swath of the active set
- importantly, the highest-population bad `O2` band is not `> 0.10`; it is the more moderate and common band `0.02–0.05`

That directly explains why the first `O2 > 0.10` guard missed too much of the real failure region.

## Key conclusion

The remaining late-time failure region in the `650 K` case is best described as:
- **moderate-temperature active cells**
- often roughly `650–1600 K` at `1.6e-05`
- later expanding into `1200–2000 K`
- with **moderate oxidizer content** (`O2` often `0.02–0.10`, not just extreme `> 0.10`)
- and less strongly product-dominated compositions than the safer cells

So a good next guard should probably not be:
- a simple `O2 > threshold` rule alone

It should more likely involve:
- a **joint state rule** using current `T` and one or two composition variables

## Practical implication

The strongest current single-knob default still remains:
- **`frozenTemperature = 650 K`**

But the next better guard is now better motivated:
- target the moderate-temperature, moderate-`O2`, lower-`H2O` region
- not just the extreme oxidizer-rich tail

## Most useful next step

The next concrete step should be to test a slightly more structured current-state guard on top of `650 K`, for example a rule focused on:
- `650 K <= T <= 1600 K`
- and `0.02 <= O2 <= 0.10`
- and possibly `H2O < 0.15` or `H2O < 0.20`

This would be a much more evidence-grounded guard than the first simple `O2 > 0.10` attempt.
