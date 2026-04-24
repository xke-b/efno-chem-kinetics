# Manuscript results/discussion prose pass: tighten the argument around H2 implementation diagnosis, H2 deployment control, and C2H4 target semantics

_Date: 2026-04-24_

## Why this was the next step

The manuscript had already accumulated enough structure, figures, tables, citations, and methods detail to support a more journal-like narrative. The next useful step was therefore not another structural addition but a prose pass on the results and discussion sections.

## Manuscript update

Updated:
- `/root/workspace/manuscript/main.tex`

This pass focused on:
- `Offline H2 reproduction and implementation diagnosis`
- `DeepFlame-coupled H2: from failure to guarded deployment`
- `C2H4 baseline establishment and runtime bridge diagnosis`
- `C2H4 data semantics: what the current best model still gets wrong`
- `Discussion`
- `Immediate remaining tasks before submission`

## What changed in the narrative

### 1. H2 offline section now reads more like an argument
The H2 offline section now makes the causal chain clearer:
- the study began as reproduction,
- but the main result became methodological,
- because the dominant early self-rollout failure was traced to a decode-contract bug,
- and fixing that bug changed the empirical interpretation of self-fed rollout.

This makes the corrected-decode figure function more like evidence in an argument rather than an isolated plot.

### 2. H2 coupled section now emphasizes solver compatibility, not just checkpoint quality
The coupled H2 section now states more directly that:
- the main early barrier was HP reconstruction failure,
- this changed the scientific question from offline accuracy to solver compatibility,
- and the hybrid fallback / threshold / risk-guard work should be read as deployment mechanisms, not ad hoc rescue patches.

### 3. C2H4 runtime section now distinguishes infrastructure failure from chemistry failure more clearly
The updated prose emphasizes that:
- reduced-rank runtime issues were scientifically useful diagnostics,
- but not trustworthy baselines,
- and only after the stock baseline and batched bridge were stabilized could the remaining discrepancies be interpreted as evidence about targets and semantics.

### 4. C2H4 semantics section now sharpens the selective-semantics conclusion
The section now states more explicitly that:
- the current best mixed model is a real positive result,
- but the remaining error pattern is structured rather than random,
- and the negative controls imply that semantics must be improved selectively rather than globally.

That is a stronger and more paper-ready claim than simply saying the current labels are imperfect.

### 5. Discussion now closes the loop across both fuels
The discussion was expanded so that it now:
- connects the H2 decode-contract result to the paper's implementation-diagnosis framing,
- connects preserve-last and HP-risk to the broader deployment-validation lesson,
- distinguishes the dominant bottleneck in H2 (deployment control) from the dominant bottleneck in C2H4 (target semantics),
- and restates the manuscript's central claim boundary more explicitly.

## Compile status

The manuscript recompiles successfully after the prose pass.

Current PDF:
- `/root/workspace/manuscript/main.pdf`

## Current takeaway

This pass does not change the evidence base, but it improves the manuscript's argumentative quality. The draft now reads more like a paper defending a specific implementation-and-deployment claim, and less like a structured summary of completed tasks.

The next likely paper-facing step is either:
- a final introduction/conclusion polishing pass, or
- one last targeted C2H4 failure-boundary figure if a sharper visual claim boundary is still desired.
