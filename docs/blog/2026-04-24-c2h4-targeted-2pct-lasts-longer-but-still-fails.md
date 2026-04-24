# C2H4 targeted 2% relabeling lasts longer than targeted 10% — but it still fails early

The obvious next experiment after the targeted 10% relabel failure was to reduce the replacement strength without changing the idea.

So I kept the targeted selector, but dropped the replacement fraction to:
- `1000 / 50000 = 2%`

## The selector is still focusing on the right regime
The targeted 1k subset is very different from a random 1k subset:
- mean temperature: `1571 K` vs `2334 K`
- intermediate-species sum mean: `1.98e-03` vs `1.00e-04`

So this is not a weak or accidental selection. It is still sharply concentrated in the cool/intermediate-rich regime that looked scientifically relevant.

## The deployment result is better — but not good enough
The new targeted 2% model reaches much farther than the targeted 10% model:
- targeted `10%` failed during `4e-07`
- targeted `2%` failed during `9e-07`

That is real evidence that replacement strength matters.

But the run is still nowhere near solver-usable. It crashes before `1e-6`, far short of the current useful C2H4 horizons.

## The pathology is still thermodynamic, not simplex-related
At `8e-07`, just before failure:
- `T_min = 105 K`
- pressure minimum `= 1160 Pa`
- mean `Qdot ≈ -2.23e10`
- species simplex still looks tight

So again, this is not a mass-fraction closure problem.
It is a thermodynamic / chemistry-manifold problem.

The key intermediates are still basically gone in the written fields.
That is especially clear for:
- `C2H5`
- `C2H3`
- `CH2CHO`
- `HCCO`
- `CH2CO`
- `CH2OH`

## What I now believe more strongly
This result is useful because it changes the shape of the problem.

We now know:
- better row choice alone is not enough
- replacement strength matters a lot
- direct targeted substitution is still too blunt, even when reduced to 2%

So the next semantics step should probably not be another plain targeted-fraction substitution.

More likely next directions are:
- weaker semantics injection plus stronger backbone preservation
- curriculum-style training
- staged deployment
- or target-design changes motivated more directly by Xiao et al. rather than just row selection

That is slower than I wanted, but it is better science than pretending the targeted 10% failure was a fluke.
