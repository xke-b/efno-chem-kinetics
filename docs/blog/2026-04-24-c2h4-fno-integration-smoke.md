# First C2H4 FNO integration smoke passed

_Date: 2026-04-24_

A short update on the new C2H4 FNO path.

The first exported C2H4 FNO bundle is no longer only an offline artifact.
I copied it into a real DeepFlame C2H4 case and ran the integrated solver with:
- `GPU on`
- `coresPerNode 8`
- `-np 8`

Result:
- the copied FNO-integrated C2H4 case runs cleanly through `5e-7`
- learned activity stays nonzero across the learned steps
- no solver fatal error appears in `solver.err`

This is not yet a claim that the FNO is good enough for the stock `5e-6` runtime target.
The current model still comes from a very small homogeneous autoignition smoke dataset.

But it is the first case-side proof that the C2H4 FNO bridge can actually load into DeepFlame and advance the real C2H4 runtime for multiple learned steps.

That lowers the integration risk substantially and makes the next questions much sharper:
- how far can this first FNO-integrated case run?
- what fails first when it stops?
- and how much better does the training data need to become to approach the stock `5e-6` baseline?
