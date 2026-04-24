# For C2H4, later model switches are better

_Date: 2026-04-24_

After the first staged deployment result looked promising, I tested when the switch should happen.

I ran the pure `dp100` model first, then switched to the gentle late-enriched curriculum model at three different times:
- `3e-6`
- `4e-6`
- `4.5e-6`

All three staged-switch runs reached `5e-6`.

The pattern was clear: **later switches are better**.

Among the tested options, switching at `4.5e-6` gave the best compromise. It stayed much closer to the pure `dp100` baseline on pressure spread, mean `Qdot`, and temperature drift than either the earlier staged switches or the full-start gentle curriculum model.

So the late-enriched model is looking less like a global replacement and more like a narrow late-horizon specialist.

That is useful because it turns the next step into an engineering problem: package a reusable switching rule, instead of trying to force one model to handle the whole trajectory from the beginning.
