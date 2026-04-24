# Manuscript introduction/conclusion pass: sharpen the opening problem statement, the paper-level contribution, and the final claim boundary

_Date: 2026-04-24_

## Why this was the next step

After the methods, figures, tables, and results/discussion prose had been strengthened, the next highest-value manuscript task was to improve the opening and closing sections.

At that stage the draft already had enough evidence, but the introduction and conclusion still underused it. The paper needed:
- a clearer opening problem statement,
- a more explicit statement of what the manuscript contributes,
- and a stronger final restatement of the claim boundary.

## Manuscript update

Updated:
- `/root/workspace/manuscript/main.tex`

This pass focused on:
- `Abstract`
- `Introduction`
- `Conclusion`

## What changed

### 1. Abstract now states the contributions more directly
The abstract now emphasizes four paper-level conclusions:
- implementation details can change scientific interpretation
- offline success does not automatically transfer to CFD deployment
- H2 now has a credible guarded deployment story
- the remaining C2H4 gap is primarily about target semantics

This makes the abstract more specific and better aligned with the actual evidence base.

### 2. Introduction now frames the paper around solver-usable learned chemistry
The introduction now distinguishes more clearly between:
- fitting chemistry data offline
- and producing a solver-usable coupled CFD component

It also states more explicitly that the manuscript's contribution is not a blanket architecture victory but an operational study of what must be true for learned stiff-chemistry surrogates to become useful in DeepFlame.

### 3. Conclusion now restates the bounded claim more strongly
The conclusion now does more than summarize sections. It closes on a more explicit methodological claim:
- learned chemistry must be evaluated as a coupled numerical component,
- not only as a dataset regressor,
- and the present paper contributes reproducible operating regimes, failure modes, and design rules rather than a final claim of complete chemistry replacement.

## Compile status

The manuscript recompiles successfully after this pass.

Current PDF:
- `/root/workspace/manuscript/main.pdf`

## Current takeaway

This pass improves the paper's framing quality. The draft now opens and closes more like a reviewable manuscript with a well-bounded contribution and a clearer take-home message.

The next likely manuscript-facing step is either:
- a final local polishing pass on wording, table/figure captions, and minor layout issues, or
- one last manuscript-grade C2H4 failure-boundary figure if a stronger visual limitation statement is still desired.
