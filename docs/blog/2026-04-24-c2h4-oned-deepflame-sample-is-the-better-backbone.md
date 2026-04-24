# The C2H4 one-dimensional DeepFlame sample looks like the better backbone — but it still needs Xiao-style balancing

After getting the DFODE-kit one-dimensional DeepFlame sampling path working for C2H4, the next obvious question was whether that manifold is actually better than the earlier Cantera-only canonical sample.

I compared three things:
- the raw oneD DeepFlame HDF5 sample
- the current Cantera canonical/interpolation/perturbation smoke sample
- the stock active C2H4 case states at `5e-6`

## The result is cleaner than I expected
The raw oneD DeepFlame sample looks like the **better physical backbone**.

Why?
Because its pressure support is much closer to the real stock case than the Cantera canonical sample:
- oneD DeepFlame mean pressure: about `101966 Pa`
- stock active mean pressure: about `101848 Pa`
- Cantera canonical mean pressure: fixed near `101325 Pa`

So in that sense, the oneD DeepFlame sample is more case-faithful.

## But it also shows exactly the Xiao problem
The raw oneD DeepFlame sample is heavily dominated by cold / weakly reacting states.
Its median temperature is only about `300.6 K`.

And its intermediate coverage is much too sparse compared with the stock active set.
For example, fraction-above-threshold values are:
- `C2H5`: `0.0526` in oneD DeepFlame vs `0.1563` in stock
- `C2H3`: `0.0484` vs `0.2660`
- `CH2CHO`: `0.0469` vs `0.1834`
- `CH2CO`: `0.0737` vs `0.2983`

That is basically Xiao’s data-imbalance story in concrete C2H4 form.

## The Cantera canonical sample is useful — but too aggressive
The current Cantera canonical sample fixes the missing-intermediate problem in direction, but overshoots badly.
Its threshold fractions for those same species are around:
- `0.66–0.78`

So the picture is now pretty clear:
- oneD DeepFlame sample = better physical backbone, but under-reactive and under-covered in the flame front
- Cantera canonical sample = useful chemistry enrichment signal, but too aggressive as a raw manifold

## What this means now
The next good data step is no longer vague.

It is not:
- keep trusting raw case pairs alone
- and not: keep relying only on the Cantera canonical generator

It is:
- take the **DeepFlame oneD sample as the backbone**
- then apply **Xiao-style interpolation and constrained perturbation** to densify the reactive zone without losing the better physical support

That feels like the first C2H4 data path in a while that is both scientifically motivated and directly grounded in the actual solver stack.
