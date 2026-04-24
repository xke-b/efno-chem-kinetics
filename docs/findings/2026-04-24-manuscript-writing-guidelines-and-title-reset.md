# Manuscript writing guidelines and title reset: add durable manuscript conventions, web-grounded writing guidance, and a more contribution-centered title

_Date: 2026-04-24_

## Why this was the next step

The manuscript workstream had reached the point where scattered notes were no longer enough. To move toward a paper that can actually be reviewed by others, the project needed:
- durable manuscript-writing guidance files,
- web-grounded conventions for title/abstract/figure/table writing,
- explicit references to those files in `AGENTS.md`,
- and a manuscript title that foregrounds substantive contribution rather than low-impact framing.

## Web search performed

I used Exa search to gather current manuscript-preparation and writing guidance from author-facing and academic-writing sources.

Representative sources reviewed:
- Frontiers: manuscript preparation and IMRaD/title/abstract guidance
  - https://www.frontiersin.org/for-authors/preparing-your-research/prepare-your-manuscript
- AAAS Science: initial manuscript preparation instructions
  - https://www.science.org/content/page/instructions-preparing-initial-manuscript
- Nature Human Behaviour: more informative titles and abstracts
  - https://www.nature.com/articles/s41562-023-01596-8
- UW–Madison Writing Center: research abstract guidance
  - https://writing.wisc.edu/handbook/assignments/writing-an-abstract-for-your-research-paper/
- Tullu (2019): title and abstract writing review
  - https://ncbi.nlm.nih.gov/pmc/articles/PMC6398294/
- APA style guidance for tables and figures
  - https://apastyle.apa.org/style-grammar-guidelines/tables-figures

## New manuscript-guidance directory

Created:
- `/root/workspace/manuscript/guidelines/`

Current file:
- `/root/workspace/manuscript/guidelines/README.md`

This file now acts as the durable local record for:
- manuscript-writing conventions
- title/abstract rules
- claim-boundary reminders
- figure/table expectations
- project-specific title policy

## AGENTS update

Updated `/root/workspace/AGENTS.md` to add explicit references to:
- manuscript directory
- manuscript writing guidance directory
- manuscript writing guidance README

Also updated the writing guidance to require:
- keeping manuscript guidance files current
- preferring contribution-centered titles
- avoiding low-impact title framings like `Reproducing`, `Towards`, or `Preliminary study` unless that framing is genuinely the main contribution

## Manuscript title reset

Updated the LaTeX manuscript title from a reproduction-centered frame to a more contribution-centered frame.

### Previous title family
- `Reproducing and Deploying Neural Stiff-Chemistry Surrogates in DeepFlame: ...`

### Updated title
- `Neural Stiff-Chemistry Surrogates in DeepFlame: Implementation Pitfalls, Coupled-Solver Safeguards, and Target Semantics for H2 and C2H4`

This title is still provisional, but it is much closer to a paper title that emphasizes substantive lessons rather than only reproduction.

## Current takeaway

The manuscript workstream now has:
- a durable local writing-guidance directory,
- explicit web-grounded manuscript conventions,
- AGENTS references that point future work back to those files,
- and a stronger title direction.

That should make subsequent manuscript work more coherent and less likely to drift back into low-impact framing.
