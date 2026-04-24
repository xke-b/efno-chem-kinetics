# Research-progress principles for this project

This note summarizes web-grounded guidance on what tends to make research both good and genuinely progressive, then translates those ideas into project-specific rules.

## Sources reviewed on 2026-04-24
- Schwab et al., *Ten simple rules for good research practice* (PLOS Comput. Biol., 2022)
- Casadevall and Fang, *Rigorous Science: a How-To Guide* (mBio, 2016)
- Vranje\v{s} and Niggemann, *Design Principles for Falsifiable, Replicable and Reproducible Empirical ML Research* (arXiv, 2024)
- Hunter, *The science of progress and the progress of science* (EMBO Reports, 2013)
- Additional discussion pieces on the value of negative results and publication bias

## Distilled principles

### 1. Good research reduces important uncertainty
Progress is not just ``more output.'' A useful study changes what a careful reader should believe or do next.

Project translation:
- prefer experiments that resolve a live design uncertainty
- avoid sweeps that only move a metric slightly without changing the next decision

### 2. A sharp hypothesis beats a vague hope
Strong empirical work starts from a testable claim with a plausible failure mode.

Project translation:
- each new experiment should answer a question like
  - ``is the bottleneck runtime infrastructure or target semantics?''
  - ``does selective relabeling help where random relabeling failed?''
- write down what outcome would count against the idea

### 3. Negative results are progress when they are diagnostic
Null or failed outcomes matter when they eliminate a tempting but wrong explanation or boundary.

Project translation:
- keep documenting failures such as
  - legacy self-rollout collapse from a decode-contract bug
  - pure chemistry-proxy early collapse
  - random partial relabeling regression
- ask what each failure rules out

### 4. Reproducibility is part of the result, not a cleanup step
Useful research should be inspectable and rerunnable.

Project translation:
- every important claim should map to scripts, artifacts, and manuscript evidence
- prefer experiments with fixed seeds, explicit contracts, and reusable tooling

### 5. Measure the thing that matters operationally
A metric is only useful if it tracks the target use case.

Project translation:
- in this project, coupled usability matters more than isolated fit alone
- prefer HP-risk, fallback fraction, runtime survival, and matched-mesh error anatomy over one-step loss alone when making deployment decisions

### 6. Minimal decisive experiments beat diffuse exploration
A good experiment is often small but discriminative.

Project translation:
- if the question is about label semantics, run a targeted relabeling scout before launching another broad architecture sweep
- if the question is about deployment, run a controlled case-side comparison before another offline benchmark expansion

## Current project implication

The current highest-value research direction is not another broad local sweep. It is selective semantics work for C2H4 guided by explicit failure anatomy:
- cool active over-drive
- hot-regime sign mismatch
- suppressed intermediate manifold

That is the standard for ``actual progress'' in the next phase: a coding experiment should either improve that diagnosis, or decisively test a targeted fix.
