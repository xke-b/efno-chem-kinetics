# The first C2H4 FNO failure looks thermodynamic before it looks off-simplex

_Date: 2026-04-24_

I repaired the C2H4 field analyzer after a useful failed attempt: some OpenFOAM fields are written as `uniform 0;`, and the earlier parser could infer the wrong cell count from unrelated integers in the file. The analyzer now uses the known `T` field length for uniform fields.

With that fixed, I compared the first FNO-integrated C2H4 case against the trusted stock baseline at `8e-7`.

The key result is sharp:
- species-simplex closure is still tight in both cases
- but the FNO-integrated case already has a severe cold-tail and much larger thermodynamic drift

At `8e-7`:
- FNO `T_min ≈ 235 K`
- stock `T_min ≈ 500 K`
- FNO mean `|ΔT|` from `5e-7` to `8e-7` is about `53.8 K`
- stock mean `|ΔT|` over the same window is about `0.26 K`

The FNO-integrated case also looks chemically underdeveloped relative to stock, with much lower `OH`, `H2O`, and `CO`.

So the best current interpretation is that this first C2H4 FNO path is not failing because of gross species-simplex collapse. It is failing because the learned state trajectory is thermodynamically wrong long before the eventual HP reconstruction crash.

That makes the next priority clearer: improve the C2H4 training-data/state-distribution alignment rather than spending too long polishing this tiny homogeneous smoke model.
