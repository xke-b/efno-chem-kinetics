# Manuscript evidence-packaging iteration: add figure/table inventory, promote C2H4 diagnostics into manuscript tables, and recompile the draft PDF

_Date: 2026-04-24_

## Why this was the next step

Once the manuscript could compile locally, the next most useful step was to improve paper readiness by converting more of the strongest current findings into manuscript-grade evidence blocks rather than leaving them only as findings pages.

## New manuscript inventory

Created:
- `/root/workspace/manuscript/FIGURE_TABLE_INVENTORY.md`

This file tracks:
- which major claims already have stable figure/table support
- which artifact files back each figure/table
- which important evidence packages are still missing

This should make future manuscript work more systematic and reduce drift.

## Expanded manuscript tables

Updated table-generation script:
- `/root/workspace/scripts/generate_manuscript_tables.py`

New generated manuscript tables:
- `/root/workspace/manuscript/tables/c2h4_error_anatomy_summary.tex`
- `/root/workspace/manuscript/tables/c2h4_chemproxy_mismatch_summary.tex`

Existing generated tables retained:
- `/root/workspace/manuscript/tables/h2_deployment_summary.tex`
- `/root/workspace/manuscript/tables/c2h4_runtime_summary.tex`

## Manuscript draft update

Updated:
- `/root/workspace/manuscript/main.tex`

The manuscript now does more than state the C2H4 claims verbally. It includes explicit manuscript tables for:
- deployment-facing C2H4 runtime comparison
- active-region C2H4 error anatomy
- chemistry-proxy label mismatch

The H2 section was also tightened slightly to make the current operating-point interpretation more explicit.

## Compile status

The manuscript recompiles successfully with `tectonic` after the updates.

Current compile output:
- `/root/workspace/manuscript/main.pdf`

The build still produces small table-layout warnings, but they are non-blocking and the document compiles successfully.

## What this changes

This iteration makes the manuscript more reviewable because it now contains:
- a clearer evidence chain from claim to artifact
- more direct quantitative support in the paper body itself
- a maintained inventory of what is already packaged versus what is still missing

## Current takeaway

The manuscript is now moving from a structured narrative draft toward a genuine reviewable results paper.

The strongest next manuscript-facing gap is now more obvious:
- the C2H4 side has a stronger packaged story than before,
- but the H2 side still needs a manuscript-ready offline corrected-decode figure and a coupled timeline/guard figure to balance the paper.
