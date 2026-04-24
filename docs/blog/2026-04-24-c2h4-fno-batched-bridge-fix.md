# The late C2H4 FNO `5e-6` issue was partly a bridge problem, and batching fixes it

_Date: 2026-04-24_

I followed the late `5e-6` C2H4 FNO caveat to the next concrete question: was the problem only the learned model, or was the case-local FNO bridge itself failing as the active learned set grew?

The answer is: the bridge was part of the problem.

The original exported FNO `inference.py` tried to run the entire active subset in one GPU batch. By `5e-6`, that active set had grown to `60316` cells, and the log showed a CUDA out-of-memory warning. The written `Qdot` field then collapsed to all zeros.

I updated the FNO exporter so the generated DeepFlame `inference.py` runs the active subset in batches and retries with smaller batches if a GPU OOM occurs.

Then I replayed the `4.9e-6 -> 5e-6` step with the batched bridge.

Result:
- no CUDA OOM line in the replay log
- still `60316` active inference cells
- written `Qdot` at `5e-6` is now nonzero again

So the late trust problem was not just "the model is bad". A meaningful part of it was that the bridge implementation was not robust to active-set growth.

This is a useful upgrade in confidence for the case-aligned C2H4 FNO path. The data-path improvement was real, and now the main observed late bridge pathology has a concrete runtime fix.
