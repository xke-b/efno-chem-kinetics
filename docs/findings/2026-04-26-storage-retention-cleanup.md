# Storage retention cleanup: experiment-run best practices, current disk profile, and a >100 GiB reclamation plan focused on superseded DeepFlame C2H4 attempts

_Date: 2026-04-26_

## Why this cleanup was necessary

The workspace had grown to roughly:
- `144G` under `/root/workspace`
- with `136G` concentrated in `/root/workspace/runs/deepflame_c2h4_smoke`

The dominant pattern was not source code or artifacts, but many full copied DeepFlame case directories from previous C2H4 deployment attempts.

## Disk profile before cleanup

### Largest top-level contributors
- `/root/workspace/runs`: `143G`
- `/root/workspace/runs/deepflame_c2h4_smoke`: `136G`
- `/root/workspace/runs/deepflame_h2_smoke`: `7.6G`
- `/root/workspace/data`: `706M`
- `/root/workspace/artifacts`: `96M`

### Largest C2H4 case families
Especially large and clearly superseded were:
- five old `np2` stock/patched baselines: about `71G`
- many early/legacy full copied FNO and curriculum runs: mostly `1.7G` to `2.2G` each
- failed delayed-switch edge cases: about `0.9G` to `1.0G` each

## Best-practice guidance consulted

I used Exa search to look for practical experiment-run and artifact-retention guidance. The most relevant themes from the retrieved material were:

1. **Keep provenance-rich summaries, not every raw run forever.**
   - Preserve metadata, run identifiers, configs, metrics, and analysis artifacts so results remain interpretable after raw bulky outputs are deleted.

2. **Delete regenerable bulk outputs once the evidence chain is extracted.**
   - Especially for experiment sweeps and failed attempts, the important retained items are usually:
     - scripts
     - configs
     - checkpoints/bundles still in use
     - evaluation summaries
     - findings/blog/manuscript references
   - not all full per-processor solver directories.

3. **For OpenFOAM-like workflows, reduce filesystem pressure and file-count growth early.**
   - Large decomposed cases generate huge numbers of files.
   - Runtime/output policy matters, but retrospective cleanup also matters once a case has been analyzed.

4. **Treat restartability as a contract.**
   - Cleanup should not remove currently referenced baseline or active deployment cases needed for the present evidence chain.

These principles fit the current project well: our docs site and JSON summaries already preserve the scientific record for many old failed attempts, so keeping every full decomposed case is not necessary.

## Retention policy used for this cleanup

### Kept
I intentionally kept:
- current stock/reference baselines still used for comparison
  - `c2h4_stock_baseline_np8_gpu_stocksrc`
  - `c2h4_cvode_baseline_np8_stockcopy`
- current best fixed-time handoff cases
  - `c2h4_enthalpy10_switch5e-07_np8`
  - `c2h4_enthalpy10_switch6e-07_np8`
- current always-learned comparison cases still referenced by recent findings
- exported model bundles, analysis JSON, docs, and manuscript artifacts

### Deleted
I targeted bulky, superseded, or invalid previous attempts whose scientific content is already retained in docs/artifacts.

## Planned deletion set

The following set was selected for deletion, with combined file payload about **`113.4 GiB`**:

- old `np2` stock / patchtest / early runtime-debug baselines
- early legacy full copied FNO integration cases
- superseded curriculum / canonical / partial-chemproxy deployment attempts
- failed delayed-switch edge cases `4e-07`, `7e-07`, and invalid off-grid `5.5e-07`

This cleanup prioritizes **space reclamation without breaking the current evidence chain**.
