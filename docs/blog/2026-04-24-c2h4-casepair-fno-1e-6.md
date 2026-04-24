# The first case-aligned C2H4 FNO reaches `1e-6`

_Date: 2026-04-24_

This is the first strong positive sign from the new C2H4 data-path work.

I trained a small FNO not on the old homogeneous autoignition smoke dataset, but on the new case-aligned CFD state-pair dataset extracted from the trusted stock C2H4 DeepFlame run.

Then I exported that model into the DeepFlame FNO bundle path and ran it in the real C2H4 case.

Result:
- the case-aligned FNO-integrated case reaches `1e-6` cleanly
- no solver fatal error appears
- the learned active-set counts stay healthy and keep increasing through the run

That is a clear improvement over the earlier homogeneous-smoke FNO, which reached `9e-7` and then failed during the `1e-6` attempt after its active-set counts collapsed.

This is not yet the final answer, because the current case-pair labels still include full CFD evolution rather than isolated chemistry-only labels. But it is the clearest evidence so far that the main bottleneck in the first C2H4 FNO attempt was the training distribution, not just the architecture or runtime wiring.

The immediate next question is now straightforward: how much farther beyond `1e-6` can this first case-aligned FNO go on the way toward the stock `5e-6` target?
