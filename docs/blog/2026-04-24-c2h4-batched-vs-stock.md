# The repaired C2H4 FNO run is now mostly a model problem, not a runtime problem

_Date: 2026-04-24_

I compared the full batched case-aligned C2H4 FNO run against the trusted stock baseline at `5e-6`.

The good news is that the big runtime pathologies are now mostly gone:
- no late CUDA OOM
- no zero-`Qdot` collapse
- no catastrophic low-temperature tail
- tight species-simplex closure remains intact

But the chemistry is still not stock-like.

At `5e-6`, the repaired full batched FNO run still has:
- mean `Qdot` about `89x` stock
- a much broader pressure range
- several late intermediates/products (`C2H5`, `C2H3`, `CH2CHO`, `CH2CO`) strongly underpredicted

So the project has crossed an important boundary. The dominant remaining bottleneck no longer looks like wiring or bridge robustness. It now looks much more like a target-quality / surrogate-quality problem.

That is useful because it sharpens the next phase: move beyond crude CFD state-pair labels and improve the learned target construction, instead of spending more time on basic runtime survival plumbing.
