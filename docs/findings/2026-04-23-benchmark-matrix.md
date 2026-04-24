# Initial benchmark matrix for EFNO reproduction

_Date: 2026-04-23_

## Benchmark order

| Stage | Benchmark | Purpose | Status |
| --- | --- | --- | --- |
| 1 | ROBER | smallest stiff ODE sanity check; verify EFNO/FNO rollout code | planned |
| 1 | POLLU | higher-dimensional stiff ODE generalization check | planned |
| 2 | H2 autoignition (7sp/16rxn) | chemistry-relevant reproduction baseline from paper | smoke dataset generated |
| 3 | DeepFlame H2 twoD_HIT_flame | first coupled-usefulness test | not started |
| 4 | DeepFlame C2H4 twoD_HIT_flame | second coupled-usefulness test | not started |

## Primary metrics

### Offline metrics
- one-step MSE / MAE
- species-wise relative error
- rollout error vs. horizon
- seen vs. unseen-condition split performance
- mass-fraction sum error
- element conservation error

Current tooling status:
- species rollout evaluator exists
- mass-fraction-sum rollout metrics exist
- element-mass rollout metrics exist
- temperature rollout metrics do not yet exist in the current DFODE-kit contract

### Coupled metrics
- solver stability / crash-free progression
- field-level relative `L2`
- drift over rollout horizon
- wall-clock savings vs. chemistry integration baseline
- whether temperature assimilation reduces drift

## Planned reproduction bundles

### Bundle A — minimal method verification
- implement vanilla FNO and EFNO on ROBER
- verify BCT and physics loss wiring
- produce rollout plots under unseen initial conditions

### Bundle B — paper-aligned chemistry benchmark
- generate 7-species H2 autoignition dataset
- run MLP baseline first
- add vanilla FNO
- add EFNO with:
  - BCT
  - element conservation loss
  - mass-fraction-sum loss
- run ablations

Current evidence:
- MLP smoke training works after safe-std normalization fix
- a provisional `fno1d` model scaffold has been added to DFODE-kit and smoke-trained successfully
- smoke rollout evaluation now exists for both MLP and provisional `fno1d`
- on the current tiny H2 smoke dataset, the MLP baseline outperforms the provisional `fno1d`

### Bundle C — coupled-usefulness transition
- map offline checkpoint format to DeepFlame inference contract
- start with H2 case small debug run
- compare learned model against current DNN setup and solver chemistry baseline

## Current assumptions ledger

1. Use `/opt/src/deepflame-dev/mechanisms/H2/ES80_H2-7-16.yaml` as the closest local match to the paper's 7-species/16-reaction H2 mechanism.
2. H2 autoignition dataset should include temperature in the state, so reactor integration must evolve energy, not species-only chemistry.
3. Constant-pressure vs. constant-volume autoignition is still ambiguous from the paper text; scripts should keep this configurable.
4. Offline reproduction precedes DeepFlame integration work.

## Executed today

- added `scripts/generate_h2_autoignition_pairs.py`
- generated a smoke dataset with shape `(80, 18)` using:
  - mechanism: `ES80_H2-7-16.yaml`
  - `n_init=8`
  - `steps=10`
  - `dt=1e-7 s`
  - reactor mode: `const_pressure`
- verified mass-fraction sums remain numerically consistent in generated pairs

## Next concrete experiments

1. keep the current best EFNO-style offline branch as corrected self-rollout with BCT-state species decoding plus `predicted_main_bct` second-step features; on H2 it now decisively beats both the seeded supervised MLP reference and the old teacher-forced legacy EFNO branch on the major rollout species, temperature, and element-mass metrics, while still trailing the supervised baseline on one-step species and element-mass MAE
2. when comparing nearby mixed-target variants, use fixed seeds by default and prefer multi-seed summaries for rollout claims
3. keep the corrected-decode search anchored to non-oracle rollout-aware branches, not the old legacy teacher-forced path: after re-baselining around the decode fix, a corrected no-rollout model is still much worse than corrected rollout-aware EFNO, so multi-step training remains genuinely useful; within the current corrected-decode neighborhood, the best H2 branch remains `self_rollout0p1_predicted_main_bct_bctdecode`, with `rollout_consistency_weight=0.1` still the strongest overall rollout tradeoff and `0.01` only a close secondary option
4. move the corrected best branch one layer closer to coupled use: on a mechanism/time-step-aligned offline benchmark for the target DeepFlame H2 case (`Burke2012_s9r23.yaml`, `dt=1e-6 s`), corrected self-rollout EFNO with predicted-main-BCT features still beats a supervised MLP decisively on final-horizon rollout species, temperature, and element-mass metrics, so this branch is now a credible default candidate for the first H2 coupling-oriented transition step
5. the first H2 deployment bridge is now practical: DFODE-kit MLP checkpoints can be exported into DeepFlame's current multi-network species checkpoint format, and the target H2 `inference.py` can load the exported checkpoint after removing hardcoded layer-size and GPU-only assumptions; however, project offline evaluation and DeepFlame still use different last-species reconstruction contracts, so deployment-facing checkpoint comparisons should now track that explicitly
6. deployment-facing evaluation for H2 must now track species postprocessing explicitly: when both the Burke-aligned benchmark and the main corrected-decode H2 holdout comparison are re-evaluated under DeepFlame's current preserve-last contract instead of closure reconstruction, earlier dramatic rollout advantages compress substantially and even the internal ranking among corrected rollout-aware branches changes
7. under the current DeepFlame-facing preserve-last contract, `teacherforced_rollout0p1_bctdecode`, `self_rollout0p1_bctdecode`, and `self_rollout0p1_predicted_main_bct_bctdecode` all looked credible in evaluator-only comparisons, but the first exported deployment-format head-to-head demotes `self_rollout0p1_predicted_main_bct_bctdecode` and makes `teacherforced_rollout0p1_bctdecode` the strongest corrected rollout-aware species candidate
8. the first actual target-case smoke test adds an important mechanism-alignment constraint: the earlier 7-species H2 candidates cannot even be loaded into the DeepFlame H2 Burke case because the solver expects 9-species inputs, so true case-side deployment work must proceed on Burke-aligned 9-species checkpoints
9. Burke-aligned exported checkpoints now clear the startup/load barrier and survive through the first DNN-driven updates in the real H2 case, but both currently fail around `3e-06` in Cantera HP reconstruction; the main coupled-use bottleneck has therefore shifted from export/runtime wiring to thermodynamic stability after learned species updates
10. pre-failure field analysis suggests that the dominant visible pathology is not gross species-simplex collapse in the written `2e-06` fields but localized thermodynamic extremeness, especially the rare very cold cells generated by the Burke supervised branch; future deployment safeguards should therefore target thermodynamic robustness, not only species normalization
11. direct HP-risk analysis on the written `2e-06` states shows that thermodynamic failure is already widespread before the observed case crash: about `10.7%` of DNN-active Burke supervised cells and `13.8%` of DNN-active Burke corrected-self-rollout cells are locally HP-unreconstructable at the next learned update, and many nominally successful reconstructions still imply absurd temperatures
12. a simple safeguard ranking is now clearer: fallback on outright HP failure is necessary but likely insufficient, whereas a hybrid policy using HP-failure fallback plus a `|ΔT| > 500 K` guard would conservatively intercept thousands of high-risk Burke cells while still leaving a substantial active subset on the learned path
13. offline snapshot simulation now provides feasibility evidence for that policy: on the written Burke `2e-06` smoke states, a hybrid strategy combining HP-failure fallback, `|ΔT| > 500 K` fallback, and a low-temperature guard reduced the rechecked next-step HP failure count to zero for both Burke candidates, which justifies moving from diagnosis into a solver-side or case-side prototype
14. the first case-side Python prototype now validates that direction: both Burke-aligned candidates can run to `5e-06` in the real DeepFlame H2 case under guarded hybrid fallback, and the corrected self-rollout Burke branch requires far less fallback than Burke supervised over the same horizon, making it the strongest current candidate for guarded deployment
15. longer-horizon case-side evidence sharpens that picture: the corrected Burke hybrid branch remains mostly learned through `1e-05` (fallback fraction about `0.308`), whereas Burke supervised is already at about `0.979` fallback by `5e-06`; however, the corrected branch still undergoes a later phase transition into near-total fallback after `1.1e-05`, so the present hybrid approach is a useful short-horizon stabilizer rather than a solved long-horizon deployment path
16. transition-window diagnosis now localizes the late failure regime more specifically: the corrected branch collapses as the DNN-active subset shifts toward slightly cooler, somewhat higher-pressure, more oxidizer-rich / less product-radical states near the activation threshold, and in that regime the exported learned update becomes predominantly HP-unreconstructable; this points toward state-aware gating or activation-region restriction as the next practical mitigation path
17. a first deployment-control ablation validates that diagnosis directly: raising `frozenTemperature` from `510 K` to `600 K` in the corrected Burke hybrid case substantially delays collapse, keeps fallback well below the old catastrophic level through much of `1e-05`–`2e-05`, and avoids ever crossing `95%` fallback by `2e-05`; the cost is reduced learned coverage, but this is the strongest current case-side mitigation lever
18. a broader frozen-temperature sweep now shows a clearer operating window: `550 K` improves over baseline but still collapses late, while `600–650 K` is the strongest current region; `600 K` looks best in parts of the mid-horizon and `650 K` gives the best learned fraction at `2e-05`, so the next local decision should likely refine inside that `600–650 K` window or add one composition-aware guard on top of it
19. the `625 K` refinement now rules out the simplest midpoint intuition: it improves some mid-horizon metrics but collapses worse than `650 K` by `2e-05`, so the best current single-threshold default for long-horizon guarded deployment is `650 K`, while `600 K` remains a plausible alternative if earlier-horizon learned coverage is weighted more heavily
20. a first composition-aware guard on top of `650 K` (current-state `T < 900 K` and `O2 > 0.10`) confirms that state-aware gating is directionally useful but that the remaining late-time failure region is broader than that single rule captures: the guard improves much of the run but still collapses to full fallback by `2e-05`, so the next high-value step is a data-driven state-conditioned failure map rather than more blind guard tweaking
21. that failure map now shows why the simple O2 rule missed too much: in the `650 K` case, the late HP-failure regime is concentrated not only in extreme-`O2` cells but also in the more common moderate-`O2` band (`~0.02–0.10`) together with moderate-temperature active states and lower-`H2O` compositions; this points toward a joint current-state guard using `T`, `O2`, and likely `H2O`, rather than another single-variable threshold
22. a first evidence-grounded joint guard confirms the direction but also exposes the next limitation: a hard rectangular `(T, O2, H2O)` exclusion box can reduce HP-failure incidence, but it over-falls back and still underperforms plain `650 K` on final learned retention, so the next serious mitigation step should likely be a small data-driven risk model rather than more hand-written boxes
23. the first tiny data-driven risk model now validates that direction: a logistic HP-risk guard built from current `(T, p, O2, H2O, OH)` is the best guard prototype tried so far, sharply reducing HP-failure incidence while preserving much more learned participation than the hand-written guards; however, at the current `0.5` threshold it still trails plain `650 K` on final learned fraction, so the next local optimization target is the risk-threshold tradeoff rather than a new guard family
24. the risk-threshold sweep now stabilizes that conclusion: among `0.4/0.5/0.6`, the `0.5` risk guard remains the best overall balance, but plain `650 K` still wins on final learned fraction at `2e-05`; this gives us two explicit deployment modes rather than one universal winner—retention-oriented `650 K`, or safety-oriented `650 K + risk-guard@0.5`
25. the supervised-branch transfer test usefully narrows the path further: the current FT650 logistic risk-guard recipe does not rescue the Burke supervised branch, which still collapses to full fallback by `1.2e-05`; this indicates the guard is useful within a viable branch but is not a generic fix for a weak deployment branch, so corrected FT650 remains the only serious H2 deployment path at present
26. if an operator architecture is revisited, prefer replacing the current `fno1d` scaffold with a more standard/operator-faithful backend before drawing stronger architecture conclusions
