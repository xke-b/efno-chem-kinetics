# Manuscript experiment-overview table: add a compact benchmark/case map to the paper and recompile the PDF draft

_Date: 2026-04-24_

## Why this was the next step

After strengthening the manuscript methods text, the next remaining readability gap was that a reviewer still had to reconstruct the paper's benchmark and case structure from prose spread across multiple sections.

The most useful next step was therefore to add a compact experiment-overview table that answers, in one place:
- which study blocks are offline vs coupled,
- which mechanism/data family each block uses,
- what split or deployment contract applies,
- and which metrics are primary for interpretation.

## What was added

Updated generator:
- `/root/workspace/scripts/generate_manuscript_tables.py`

New generated table:
- `/root/workspace/manuscript/tables/experiment_overview.tex`

Current rows cover:
- offline H2 holdout benchmark
- coupled H2 Burke deployment case
- stock C2H4 baseline
- best learned C2H4 deployment case

## Manuscript update

Updated:
- `/root/workspace/manuscript/main.tex`

The new table is inserted in the `Methods and evaluation protocol` section so the reader sees the benchmark/case map before the paper returns to detailed results.

## Compile status

The manuscript recompiles successfully after adding the table.

Current PDF:
- `/root/workspace/manuscript/main.pdf`

The new table introduces some additional `underfull` box warnings because the content is dense, but these are layout warnings rather than build failures. The paper still compiles successfully and the table serves its intended organizational purpose.

## Why this improves the manuscript

This table materially improves paper usability:
- it reduces the cognitive load required to track which result belongs to which benchmark or deployment regime,
- it makes key evaluation contracts visible in one place,
- and it better supports the manuscript's framing as an implementation-and-deployment study rather than a single benchmark report.

## Current takeaway

The manuscript now has:
- citations,
- methods/protocol text,
- a benchmark/case overview table,
- H2 and C2H4 figures/tables,
- and a compiled PDF draft.

The next likely manuscript-facing step is no longer basic structure. It is either:
- tightening the prose of the results/discussion sections into a more journal-like argument, or
- adding one last targeted manuscript-grade C2H4 failure figure if that would sharpen the claim boundary further.
