# Manuscript first PDF compile: local LaTeX toolchain installed, manuscript tables generated, and draft PDF compiled successfully

_Date: 2026-04-24_

## Why this mattered

The project goal now explicitly includes a reviewable academic manuscript in LaTeX compiled to PDF. That makes local compilation a real workflow requirement, not a future convenience.

## What was done

### 1. Installed a local LaTeX toolchain
Installed in the `deepflame` environment:
- `tectonic`

This provides a reproducible path to local PDF builds without requiring a full system TeX installation.

### 2. Added manuscript-table generator
New script:
- `/root/workspace/scripts/generate_manuscript_tables.py`

Current outputs:
- `/root/workspace/manuscript/tables/h2_deployment_summary.tex`
- `/root/workspace/manuscript/tables/c2h4_runtime_summary.tex`

These convert existing experiment artifacts into manuscript-ready LaTeX tables.

### 3. Updated the manuscript draft
Updated:
- `/root/workspace/manuscript/main.tex`

The draft now:
- uses a more contribution-centered title
- includes actual generated tables
- includes a manuscript figure from the current best C2H4 vs stock comparison
- is no longer only an outline skeleton

### 4. Compiled the manuscript to PDF
Compiled successfully with:
- `tectonic --keep-logs --keep-intermediates main.tex`

Compiled PDF artifact:
- `/root/workspace/artifacts/manuscript/efno_h2_c2h4_deepflame_draft_2026-04-24.pdf`

## Current title direction

The title was changed away from low-impact reproduction framing.

### Current manuscript title
- `Neural Stiff-Chemistry Surrogates in DeepFlame: Implementation Pitfalls, Coupled-Solver Safeguards, and Target Semantics for H2 and C2H4`

This remains provisional, but it is a better match to the actual contribution story.

## Build status

The manuscript now compiles successfully.

The current build still emits some minor table layout warnings (`underfull` / small `overfull` boxes), but these are presentational issues, not build blockers.

## Current takeaway

The manuscript workstream has crossed an important threshold:
- there is now a local LaTeX compile path
- stable manuscript table generation exists
- a first draft PDF has been produced

That makes future manuscript work much more concrete: the next updates should keep improving a real paper artifact instead of only accumulating notes.
