# Repeating the better C2H4 subset more often did not help

_Date: 2026-04-24_

I tested a simple proxy for weighted training on the C2H4 case-pair data:
- one copy of the unfiltered dataset
- two copies of the better `dp100` dataset

The model stayed solver-usable to `5e-6`, so this was a real runtime comparison, not a crash artifact.

But the result regressed.

Compared with the simpler `1:1` mixed dataset, the `1:2` dp100-heavy mix had:
- higher mean `Qdot`
- a worse pressure tail
- worse mean `|ΔT|` drift

So naive oversampling of the better subset is not the weighting trick we want. This is another case where a cleaner offline fit did not translate into a better coupled-solver outcome.

That pushes the next step away from blind duplication and closer to a deeper target-construction question, especially around the missing late intermediates/products that none of these subset games are recovering.
