# DeepFlame H2 current deployment recommendation: use plain FT650 for retention-oriented runs, or generate FT650 + logistic risk-guard@0.5 for safety-oriented runs

_Date: 2026-04-23_

## Purpose

This note turns the current Burke H2 smoke-run evidence into a short operator-facing recommendation.

## Recommended deployment modes

### 1. Retention-oriented default
Use the corrected Burke case with a higher activation threshold and no extra risk guard:
- case: `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650`

Why:
- strongest current end-of-run learned fraction at `2e-05`
- current best single-knob deployment default

Use this mode when the main priority is keeping the learned branch active as much as possible.

### 2. Safety-oriented guarded mode
Use the corrected Burke FT650 case plus the logistic risk guard at threshold `0.5`:
- generated case target example: `/root/workspace/runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard_generated_from_config`
- risk config: `/root/workspace/artifacts/models/deepflame_h2_ft650_logistic_hp_risk_v1.json`
- generator: `/root/workspace/scripts/create_deepflame_hybrid_case.py`

Why:
- best current safety-oriented guarded prototype
- sharply reduces HP-failure incidence relative to plain FT650
- more credible than the hand-written guard variants

Use this mode when the main priority is reducing HP-risk, even if some learned retention is sacrificed.

## Exact generation command for the safety-oriented mode

From `/root/workspace`:

```bash
python scripts/create_deepflame_hybrid_case.py \
  --src-case runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650 \
  --dst-case runs/deepflame_h2_smoke/burke_corrected_self_rollout_predmainbct_ft650_riskguard_generated_from_config \
  --frozen-temperature 650 \
  --risk-config artifacts/models/deepflame_h2_ft650_logistic_hp_risk_v1.json \
  --overwrite
```

This reproduces the validated FT650 risk-guard case exactly.

## Exact run commands

After selecting either the plain FT650 case or the generated risk-guard case:

```bash
source /opt/openfoam7/etc/bashrc
source /opt/conda/etc/profile.d/conda.sh
conda activate deepflame
source /opt/src/deepflame-dev/bashrc

cd /root/workspace/runs/deepflame_h2_smoke/<CASE_NAME>
rm -rf processor* [1-9]*
blockMesh > log.blockMesh 2>&1
decomposePar > log.decomposePar 2>&1
mpirun --allow-run-as-root -np 4 dfLowMachFoam -parallel > run.log 2> solver.err
```

## Current recommendation summary

If you need one default today:
- use **plain FT650** for retention-oriented corrected-branch deployment

If you need the safer of the currently tested guarded policies:
- use **FT650 + logistic risk-guard@0.5** generated from `deepflame_h2_ft650_logistic_hp_risk_v1.json`

## Not recommended as primary deployment choices

Based on current evidence, do not treat these as the main forward path:
- Burke supervised branch as a competing deployment candidate
- simple `O2`-only hand-written guard
- hand-written joint `(T, O2, H2O)` box guard
- lower frozen-temperature variants below the current `600–650 K` operating region
