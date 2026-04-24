# Manuscript outline and claim boundary reset: there is enough for a reviewable paper now, but it should be written as a rigorous partial-results deployment paper

_Date: 2026-04-24_

## Why this was the right next step

After asking whether the current results are strong enough for an academic manuscript, the most useful immediate follow-up was not another experiment first.

It was to make the answer operational:
- define the paper we can honestly write now,
- state what claims are already supported,
- state what claims are still too strong,
- and create a manuscript scaffold so the project can accumulate directly toward a preprint instead of only toward more notes.

## New manuscript scaffold

- `/root/workspace/manuscript/main.tex`

This is a first LaTeX manuscript skeleton organized around the strongest current evidence.

## Core manuscript framing

The current work is best framed as a paper about:
- reproducing EFNO-style stiff-chemistry surrogates,
- diagnosing implementation pitfalls,
- testing deployment in DeepFlame,
- and showing why target semantics matter in coupled CFD usefulness.

This is **not** yet framed as a final paper claiming solved C2H4 chemistry replacement.

## Claim boundary

### Claims that are already supportable

#### 1. Implementation correctness matters materially
The H2 work supports a strong claim that transformed-state decode details can change the rollout story materially. The corrected BCT-state decode path is not a cosmetic patch; it changes the empirical regime.

#### 2. Offline success does not directly predict coupled usefulness
The H2 and C2H4 runs together support a strong deployment-facing claim that:
- offline metrics,
- project-side evaluation contracts,
- and true DeepFlame coupled behavior
can disagree substantially.

#### 3. H2 requires deployment safeguards, not only a better offline model
The hybrid fallback, frozen-temperature gating, and logistic risk-guard work already support a credible H2 deployment section.

#### 4. C2H4 is currently target-limited more than sweep-limited
The C2H4 evidence now supports a strong partial-results claim that data construction and label semantics appear to dominate the remaining error structure.

### Claims that should still be avoided

#### Avoid claiming:
- solved C2H4 replacement chemistry
- broad final superiority over standard chemistry integration in coupled CFD
- final architecture-level victory of EFNO/FNO over alternatives in all relevant settings

Those would overstate the current state of the evidence.

## Recommended paper type

The best current manuscript is a:
- **reviewable partial-results paper / preprint**
- focused on reproducibility, deployment diagnostics, and target semantics

A good title family is something like:
- *Reproducing and Deploying Neural Stiff-Chemistry Surrogates in DeepFlame: Implementation Pitfalls, Coupled-Solver Safeguards, and the Importance of Target Semantics*

## Current section plan

The scaffold organizes the paper around:
1. introduction and motivation
2. related work / EFNO context
3. reproducible workflow and software stack
4. offline H2 reproduction and decode-bug diagnosis
5. coupled H2 deployment and guarding
6. C2H4 baseline establishment and runtime bridge fixes
7. C2H4 data semantics and remaining error anatomy
8. discussion and limitations
9. conclusion

## Immediate practical value

This is useful now because it changes the project from “many findings pages” into “a growing manuscript with defined claims.”

That helps in three ways:
- it clarifies which experiments are still manuscript-critical,
- it limits over-claiming,
- and it gives a concrete place to accumulate figures and tables.

## Important limitation

The current environment does **not** yet have a LaTeX toolchain available:
- `pdflatex` / `latexmk` were not found locally

So this step produced the manuscript scaffold and claim structure, but not a compiled PDF yet.

## Current takeaway

The project now has enough evidence for a reviewable manuscript **if** it is written honestly as a rigorous partial-results deployment paper.

The next manuscript-facing steps should be:
- convert current key findings into stable figures/tables,
- add one more label-semantics-driven experiment if possible,
- and then install a LaTeX toolchain to compile the draft.
