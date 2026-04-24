# The real C2H4 bottleneck is now visible: wrong source-term behavior in two different regimes

_Date: 2026-04-24_

I followed the priority reset with the next diagnostic that actually mattered: compare the current best learned C2H4 model (`dp100 + canonical@0.2`) directly against the stock DeepFlame run on the matched mesh at `5e-6`.

This clarified the remaining problem a lot.

The best mixed model is not mainly failing because it activates in the wrong part of the domain. Its active region overlaps stock closely.

The problem is what it does **inside** that active region:
- in cooler active cells, it over-drives chemistry badly
- in the hot active bulk, it often gets the source-term sign wrong
- and it still heavily suppresses key late intermediates like `C2H5`, `C2H3`, `CH2CHO`, and especially `CH2CO`

That is a much stronger argument that the next bottleneck is target semantics, not another local mix-ratio sweep.
