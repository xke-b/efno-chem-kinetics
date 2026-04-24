# Exa-search sweep: no public EFNO paper code found yet, but close neural-operator references do exist

_Date: 2026-04-23_

## Why this search mattered

The EFNO paper leaves several practical implementation details ambiguous:
- retained Fourier modes
- hidden width / channel width
- optimizer and schedule
- exact backbone implementation details
- whether public code exists that could resolve ambiguity faster than blind reconstruction

Because reducing this uncertainty is high value, I used the `exa-search` skill as a priority action.

## What I searched for

Main search themes:
1. the exact EFNO paper title plus `GitHub`, `code`, `implementation`
2. the paper DOI `10.1016/j.combustflame.2024.113847`
3. author-name + code searches
4. the related reference from the EFNO paper:
   - Goswami et al., *Learning stiff chemical kinetics using extended deep neural operators*

## What was found

### 1. No clear public repository for the EFNO paper itself
Searches for the exact paper title and DOI did **not** surface a repository that clearly corresponds to:
- Weng et al. (2025)
- *Extended Fourier Neural Operators to learn stiff chemical kinetics under unseen conditions*

This does **not** prove no code exists, but at this point there is no publicly obvious implementation artifact located through Exa.

### 2. A closely related public codebase exists for the cited DeepONet predecessor paper
Exa surfaced:
- `https://github.com/somdattagoswami/Approximating-StiffKinetics`

This repository is explicitly for:
- *Learning stiff chemical kinetics using extended deep neural operators*

This is useful because it provides:
- a concrete prior art codebase for stiff-chemistry operator learning
- public evidence about how a related paper organized examples and datasets
- a potential source of benchmark conventions even though it is DeepONet-based, not FNO-based

### 3. General FNO implementation references are available
Exa also surfaced the `neuraloperator` library:
- `https://github.com/NeuralOperator/neuraloperator`

This is useful as a robust implementation reference for standard FNO machinery when paper-specific details are missing.

### 4. Bibliographic sources confirm the EFNO paper and its reference graph
Exa surfaced bibliographic pages such as:
- ADS entry for the EFNO paper
- OUCI bibliographic page with references

The OUCI entry was especially useful because it made the paper's cited lineage easier to inspect and confirmed that the EFNO paper explicitly cites:
- FNO references
- DeepONet references
- the extended deep neural operator stiff-chemistry paper

## Practical implication

The current best evidence-based path is:
1. **do not assume hidden public EFNO code exists**
2. use the paper text as the primary contract
3. use:
   - the public DeepONet stiff-chemistry repo for neighboring benchmark conventions
   - the `neuraloperator` ecosystem for standard FNO implementation choices
4. explicitly document every unresolved EFNO-specific degree of freedom

## Most useful conclusion

The search reduced uncertainty in a meaningful way:
- there is no immediately discoverable official EFNO codebase to short-circuit reproduction
- but there are enough nearby public resources to make the reconstruction less blind

This supports the current strategy of:
- faithful paper-note extraction
- incremental reproduction
- careful use of neighboring operator-learning codebases only as references, not as silent substitutes

## Relevant URLs found

- EFNO paper bibliographic entry: `https://ui.adsabs.harvard.edu/abs/2025CoFl..27213847W/abstract`
- EFNO DOI/index page: `https://ouci.dntb.gov.ua/en/works/73m3yYXl/`
- Related stiff-chemistry DeepONet code: `https://github.com/somdattagoswami/Approximating-StiffKinetics`
- General FNO library: `https://github.com/NeuralOperator/neuraloperator`

## Decision update

Until stronger evidence appears, continue treating the EFNO paper as a **specification-first reproduction problem**, not a code-reimplementation problem.
