# Manuscript methods/protocol pass: make benchmark definitions, deployment contracts, and evaluation logic explicit in the paper draft

_Date: 2026-04-24_

## Why this was the next step

After adding figures, tables, citations, and a compiled PDF, the next main weakness in the manuscript was methodological explicitness. The paper had results and interpretation, but it still needed a clearer statement of:
- what benchmark/case definitions were actually used,
- how offline and coupled evaluations differ,
- why some ranking changes are methodological rather than accidental,
- and which runtime contracts matter for interpreting the evidence.

## Manuscript update

Updated:
- `/root/workspace/manuscript/main.tex`

Added a new section:
- `Methods and evaluation protocol`

## What the new section makes explicit

### 1. Offline H2 benchmark definition
The manuscript now states more clearly that:
- the offline H2 benchmark is built from autoignition trajectories using a seven-species hydrogen mechanism,
- holdout splits are defined by initial-condition trajectory rather than random sample shuffling,
- fixed seeds are used for nearby comparisons,
- evaluation includes both one-step metrics and long-horizon rollout/physical-consistency metrics.

### 2. DeepFlame-facing H2 contract logic
The draft now states explicitly that:
- Burke-aligned nine-species export is the coupled target,
- species-count alignment is a hard requirement,
- `closure` vs `preserve_last` is part of the evaluation contract,
- and the preserve-last contract can materially change offline ranking interpretation.

This is important because the H2 story depends not only on model quality, but also on evaluating under the same postprocessing rule used by DeepFlame deployment.

### 3. C2H4 baseline and runtime gating logic
The draft now states that:
- the stock-style trusted baseline is the `np=8`, GPU-enabled DeepFlame regime,
- learned-model conclusions are only interpreted after runtime bridge pathologies were fixed,
- and C2H4 datasets are discussed as a sequence of increasingly deployment-relevant label families rather than one monolithic training set.

### 4. Deployment-facing metric logic
The manuscript now states more directly that:
- H2 coupled decisions are driven by HP-failure fractions, learned/fallback fractions, and operating windows,
- C2H4 coupled decisions are driven by survival to the stock horizon plus matched-mesh thermochemical comparisons,
- and negative results are treated as methodological evidence.

## Why this improves the paper

This pass does not add new experimental results, but it improves the paper in a review-relevant way:
- it makes the evidence chain easier to audit,
- it reduces ambiguity about what is actually being compared,
- it turns important hidden implementation/evaluation contracts into explicit method text,
- and it helps justify why several negative results belong in the paper.

## Current takeaway

The manuscript is now materially better not just as a collection of results, but as a methods-driven implementation study. The next likely high-value manuscript step is either:
- tightening the H2 and C2H4 methods with a compact experiment-overview table, or
- expanding the result/discussion prose into a more journal-like narrative.
