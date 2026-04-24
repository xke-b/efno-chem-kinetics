# Extending the first C2H4 FNO integration case toward `1e-6`: it survives through `9e-7` and then fails in HP reconstruction during the `1e-6` attempt

_Date: 2026-04-24_

## Why this was the next step

After the first copied C2H4 FNO-integrated DeepFlame case ran cleanly through `5e-7`, the next useful question was simple:
- how far does this first integrated FNO case go before it fails, and what fails first?

## Case

- `/root/workspace/runs/deepflame_c2h4_smoke/c2h4_fno_smoke_integration`

The case remained in the stock-style trusted runtime regime:
- `GPU on`
- `coresPerNode 8`
- `numberOfSubdomains 8`
- `mpirun -np 8`

I extended the copied FNO case from `5e-7` toward `1e-6`.

## Result

The case continued successfully through:
- `6e-7`
- `7e-7`
- `8e-7`
- `9e-7`

It then failed during the next step toward `1e-6`.

So the first integrated C2H4 FNO case now has a demonstrated survival horizon of:
- **`9e-7` completed**
- **failure during the `1e-6` attempt**

## Failure mode

The failure was not a Python import problem, not a model-loading problem, and not an MPI/GPU communication crash.

It failed in thermodynamic reconstruction:
- `CanteraError thrown by ThermoPhase::setState_HPorUV (HP): No convergence in 500 iterations`
- propagated from:
  - `dfChemistryModel::correctThermo()`

This is structurally similar to the HP-reconstruction instability family previously seen in the H2 integration work, even though the C2H4 stock baseline itself is much healthier.

## Pre-failure evidence

At the final successful logged step before the crash (`8e-7` block in the log), DeepFlame reported:
- `real inference points number: 10200`
- `min/max(T) = 235.021, 1845.63`

At the next step (`9e-7` block), it still had nonzero learned activity:
- `real inference points number: 5346`

But then HP reconstruction failed on at least two ranks with states such as:
- rank 5:
  - starting temperature: `433.32 K`
  - pressure: `106116 Pa`
  - target enthalpy: `389980`
- rank 6:
  - starting temperature: `609.88 K`
  - pressure: `106368 Pa`
  - target enthalpy: `387802`

The active-set counts across this case now look like:
- `2e-7`: `33508`
- `3e-7`: `33508`
- `4e-7`: `33532`
- `5e-7`: `33509`
- `6e-7`: `33564`
- `7e-7`: `33630`
- `8e-7`: `10200`
- `9e-7`: `5346`

That sharp active-set collapse is itself a useful signal: the model is not merely running until a random crash; the learned region is shrinking materially before thermodynamic failure.

## What this means

This is still real progress.

The project has now established that the first C2H4 FNO integration path:
- loads correctly
- runs in the trusted stock-style `np=8` GPU regime
- survives multiple learned steps in the real C2H4 case
- fails first in **thermodynamic consistency / HP reconstruction**, not in basic runtime wiring

That narrows the next diagnosis substantially.

## Important limitation

This first FNO was trained only on a very small homogeneous autoignition dataset. So this early HP-type failure should not be overinterpreted as an indictment of FNOs in general. It is more likely evidence that the current training data and target contract are not yet case-aligned enough for the C2H4 CFD runtime.

## Artifacts

- `/root/workspace/artifacts/experiments/deepflame_c2h4_smoke_analysis/c2h4_fno_smoke_integration_1e-6_attempt_summary.json`

## Most useful next step

Build the next diagnosis around this now-localized failure family:
1. analyze the last successful written C2H4 FNO-integrated fields around `8e-7` / `9e-7`
2. compare them against the stock C2H4 baseline at the same horizon
3. then decide whether the next intervention should be:
   - a guarded fallback prototype for FNO integration, or
   - a better case-aligned C2H4 training dataset, which is likely the higher-value path
