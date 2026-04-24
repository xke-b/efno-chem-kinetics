# Manuscript preparation and writing guidelines

This directory collects manuscript-writing guidance, title/abstract conventions, and paper-assembly notes for the project paper on **EFNO applied to H2 and C2H4 surrogate chemistry in CFD**.

## Current purpose
- keep manuscript-writing guidance in durable project files
- separate writing conventions from experiment findings
- support consistent updating of `manuscript/main.tex`
- support later peer review and journal adaptation
- keep a project-local record of what counts as good research progress for the active program

## Related guidance files
- manuscript writing conventions:
  - `/root/workspace/manuscript/guidelines/README.md`
- research-progress principles:
  - `/root/workspace/manuscript/guidelines/research-progress-principles.md`

## Current working title policy
Prefer titles that foreground the paper's substantive contribution.

Avoid low-impact framing such as:
- `Reproducing ...`
- `Towards ...`
- `Preliminary study ...`

unless the manuscript's main contribution is explicitly a reproducibility or benchmark study.

For this project, titles should emphasize:
- EFNO / neural stiff-chemistry surrogates
- H2 and C2H4 in CFD / DeepFlame
- deployment lessons
- implementation pitfalls / safeguards
- target semantics and coupled usefulness

## Web-guided writing conventions gathered on 2026-04-24

### 1. Use a standard scientific structure unless the target venue requires otherwise
Across author guidance and writing resources, the default recommendation remains IMRaD:
- Introduction
- Methods
- Results
- Discussion

Useful source:
- Frontiers, "How to prepare your manuscript"
  - https://www.frontiersin.org/for-authors/preparing-your-research/prepare-your-manuscript

### 2. Write title and abstract late, but design them deliberately
Common recommendations across publisher guidance and writing references:
- draft title/abstract after the paper body is coherent
- make the title specific, accurate, and not overstated
- keep the abstract self-contained
- avoid citations and unnecessary abbreviations in the abstract
- ensure title and abstract match the actual evidence and scope

Useful sources:
- Frontiers, manuscript preparation guidance
- UW–Madison Writing Center, abstract guidance
  - https://writing.wisc.edu/handbook/assignments/writing-an-abstract-for-your-research-paper/
- Tullu, 2019, title and abstract writing
  - https://ncbi.nlm.nih.gov/pmc/articles/PMC6398294/

### 3. Avoid titles that overstate evidence
Nature Human Behaviour's title/abstract guidance is especially relevant:
- do not use titles that imply broader generality than the evidence supports
- include scope/population/context when that matters
- make the abstract more informative about evidence strength

Useful source:
- Nature Human Behaviour, "Writing more informative titles and abstracts"
  - https://www.nature.com/articles/s41562-023-01596-8

### 4. Prefer informative, contribution-centered titles
Based on the sources above, good titles should:
- name the problem and setting
- signal the main contribution or lesson
- avoid empty verbs like `towards`, `exploring`, `a study of`
- avoid vague cause/effect framing without the actual finding

For this project, good title ingredients include:
- neural stiff-chemistry surrogates
- DeepFlame / CFD
- H2 and C2H4
- implementation lessons
- coupled-solver safeguards
- target semantics

### 5. Tables and figures should carry real argumentative load
Best-practice guidance consistently emphasizes that tables and figures should:
- clarify results rather than repeat prose mechanically
- be interpretable with caption plus body/legend
- use consistent units and labels
- highlight comparison, not just dump numbers

Useful sources:
- APA tables and figures guidance
  - https://apastyle.apa.org/style-grammar-guidelines/tables-figures
- General publishing guidance on table/figure clarity
  - https://journal-publishing.com/guide/designing-tables-figures

### 6. Negative results and limitations should be explicit
For this manuscript, this is especially important because a major contribution is diagnostic:
- implementation bugs changed conclusions
- deployment failures exposed offline/deployment mismatch
- C2H4 label-semantics fixes are not yet solved

The paper should therefore distinguish clearly between:
- validated results
- useful failures
- open problems

## Project-specific writing rules

### Title rule
The title should foreground substantive contribution, not just replication.

Current preferred title family:
- `Neural Stiff-Chemistry Surrogates in DeepFlame: Implementation Pitfalls, Coupled-Solver Safeguards, and Target Semantics for H2 and C2H4`

### Abstract rule
The abstract should explicitly state:
- the problem setting: H2 and C2H4 surrogate chemistry in CFD / DeepFlame
- the main positive result for H2
- the main partial/diagnostic result for C2H4
- the main methodological lesson: implementation details, deployment validation, and target semantics matter

### Claim-boundary rule
Do not claim:
- solved C2H4 surrogate chemistry replacement
- broad final superiority in all CFD-coupled settings
- general EFNO dominance without qualification

Do claim when supported:
- corrected implementation materially changed H2 conclusions
- deployment safeguards were necessary for H2 coupled usefulness
- current C2H4 bottleneck is strongly tied to target semantics and label structure

### Evidence-packaging rule
Every major manuscript claim should map to:
- at least one stable artifact file
- at least one findings page
- preferably one table or figure in `manuscript/`

## Next writing tasks
- keep refining the title away from low-impact framing
- continue converting findings into manuscript-ready figures/tables
- add references/citations to the LaTeX draft
- keep this directory updated whenever manuscript conventions or target-journal assumptions change
