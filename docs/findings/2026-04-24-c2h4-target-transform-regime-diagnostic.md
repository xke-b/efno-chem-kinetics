# C2H4 target-transform regime diagnostic: Xiao-style scale-separation pathology is already visible in the current BCT-delta targets

_Date: 2026-04-24_

## Why this was the next step

After the targeted `2%` relabeling test, the most useful unresolved question was whether the remaining C2H4 failure is still partly a **target representation** problem, not only a data-selection problem.

Xiao et al. (2026) argue that state-based nonlinear target transforms can lose resolution in low-temperature / small-delta regimes, and that a power transform applied directly to the physical concentration change can recover that resolution. Our current DFODE training path for species-only C2H4 uses:

- inputs: `T`, `P`, and BCT-encoded species state
- targets: `BCT(Y_next) - BCT(Y_current)` for the modeled main-species block

That is not identical to Xiao’s Box-Cox setup, but it is a close enough state-transform-on-both-ends construction that the same failure mode is worth testing directly.

So this step was a **diagnostic**, not yet a new training run:
- quantify whether the current BCT-delta target depends strongly on the current state in low-temperature / tiny-delta regimes
- compare it against a Xiao-style power transform on the physical delta

## Script and artifact

Script:
- `/root/workspace/scripts/analyze_c2h4_target_transform_regimes.py`

Artifact:
- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_target_transform_regime_analysis.json`

Datasets analyzed:
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100.npy`
- `/root/workspace/data/c2h4_case_pairs_smoke_dp100_plus_canonical_r0p2.npy`

The analysis compares:
- current target: `BCT(Y_next) - BCT(Y_current)`
- Xiao-style candidate target: `sign(ΔY) * |ΔY|^0.1 / 0.1`

For selected species and temperature regimes, it measures whether the transformed target tracks:
- the physical delta magnitude `|ΔY|`
- or the current-state concentration `Y(t)`

## Main result

Yes: the Xiao-style pathology is already visible in our C2H4 target formulation.

In low-temperature small-delta regimes, the current BCT-delta target often shows:
- **strong dependence on current species level**, and
- **weak or even negative correlation with the true physical delta magnitude**

By construction, the power-transformed physical delta retains almost perfect monotone correspondence with `|ΔY|`.

## Concrete examples

### Best current baseline dataset: `dp100 + canonical@0.2`

For low-temperature `O2` targets with `|ΔY| in [1e-15, 1e-12)`:
- count: `336`
- corr(`log Y(t)`, `log |BCT-delta|`) = **`-0.962`**
- corr(`log |ΔY|`, `log |BCT-delta|`) = **`-0.533`**
- corr(`log |ΔY|`, `log |power-delta|`) = **`1.0`**

Interpretation:
- in this regime, the current target is more strongly driven by the current state than by the physical delta we want to learn
- and the mapping can even invert local ordering with respect to true delta magnitude

For low-temperature `HCCO` with `|ΔY| in [1e-15, 1e-12)`:
- count: `384`
- corr(`log Y(t)`, `log |BCT-delta|`) = **`-0.945`**
- corr(`log |ΔY|`, `log |BCT-delta|`) = **`-0.789`**
- corr(`log |ΔY|`, `log |power-delta|`) = **`1.0`**

For low-temperature `CH2OH` with `|ΔY| in [1e-15, 1e-12)`:
- count: `192`
- corr(`log Y(t)`, `log |BCT-delta|`) = **`-0.960`**
- corr(`log |ΔY|`, `log |BCT-delta|`) = **`-0.382`**
- corr(`log |ΔY|`, `log |power-delta|`) = **`1.0`**

### Pure `dp100` dataset

The same failure mode appears there too, though the strongest examples shift somewhat by species/bin.

For low-temperature `CH2CHO` with `|ΔY| in [1e-08, 1e-06)`:
- count: `367`
- corr(`log Y(t)`, `log |BCT-delta|`) = **`-0.733`**
- corr(`log |ΔY|`, `log |BCT-delta|`) = **`-0.133`**
- corr(`log |ΔY|`, `log |power-delta|`) = **`1.0`**

For low-temperature `HCCO` with `|ΔY| in [1e-10, 1e-08)`:
- count: `760`
- corr(`log Y(t)`, `log |BCT-delta|`) = **`-0.665`**
- corr(`log |ΔY|`, `log |BCT-delta|`) = **`-0.130`**
- corr(`log |ΔY|`, `log |power-delta|`) = **`1.0`**

## Interpretation

This does **not** prove that a power-transformed target will immediately solve the full C2H4 deployment problem.

But it does prove something important:

- the current BCT-delta target is not a neutral parameterization in the low-temperature multiscale regime
- in several scientifically relevant C2H4 channels, it is partly encoding the current-state level more strongly than the actual physical step size
- this is exactly the kind of target-geometry distortion Xiao et al. warn about

That gives us a much stronger justification for a next implementation step than we had before.

## What this changes

Before this diagnostic, “try a Xiao-style scale-separated target” was plausible but still somewhat speculative.

After this diagnostic, it is now a **directly evidenced next experiment**.

The forward path should likely include a new offline training ablation that replaces the current species target with a power-transformed physical delta, for example:
- `target_mode = species_power_delta`
- optionally later as a hybrid rule by regime, as Xiao did for low-temperature states

## Current takeaway

The current C2H4 bottleneck is still primarily data/target quality, but we now have sharper evidence that **target formulation itself is part of that bottleneck**.

The next useful implementation step is no longer just “more data preparation” in the abstract. It is specifically:
- test a Xiao-style scale-separated delta target in the DFODE/DeepFlame path,
- first offline, then in-case if the offline behavior is credible.
