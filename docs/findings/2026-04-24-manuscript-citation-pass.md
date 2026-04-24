# Manuscript citation pass: add a first bibliography, cite EFNO and local related papers, and compile the referenced draft PDF

_Date: 2026-04-24_

## Why this was the next step

After packaging the main H2 and C2H4 evidence blocks, the next highest-value manuscript task was to turn the draft into a referenced paper rather than a citation-free internal summary.

## What was added

Created bibliography file:
- `/root/workspace/manuscript/references.bib`

Current references added:
- EFNO paper by Weng et al.
- comprehensive DeepFlame/combustion-chemistry integration paper by Li et al.
- physics-aware augmentation paper by Xiao et al.
- DFODE-kit paper by Li et al.
- NH3/H2 coupled-validation paper by Wu et al.

## Manuscript updates

Updated:
- `/root/workspace/manuscript/main.tex`

Main changes:
- added citations in the introduction, background, workflow, C2H4 baseline, C2H4 data-semantics, and discussion sections
- added bibliography commands
- preserved the existing H2/C2H4 evidence packaging and figure/table structure

## Compile status

Compiled successfully with BibTeX via Tectonic.

Current outputs in `manuscript/` include:
- `main.pdf`
- `main.bbl`

The cited draft now builds successfully and produces a manuscript PDF with a bibliography.

## Current takeaway

This does not finish the paper, but it changes the manuscript qualitatively:
- it is now a referenced scientific draft rather than only a structured project summary
- the narrative is better tied to the EFNO paper and nearby combustion-surrogate literature
- the next manuscript step can focus more on methods clarity and claim tightening instead of basic citation plumbing
