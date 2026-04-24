# The first paper-inspired canonical C2H4 data path works — maybe too well

_Date: 2026-04-24_

I implemented a first smoke prototype of the data-generation strategy suggested by the other local papers:
- solve a canonical 1D C2H4 flame
- densify reactive regions by interpolation in temperature space
- perturb states off the manifold
- re-label them with Cantera
- filter aggressively with simple physical checks

The good news is that it clearly does what we wanted on one key point: it produces much richer coverage of the missing late intermediates like `C2H5`, `C2H3`, `CH2CHO`, and `CH2CO` than the current case-pair `dp100` dataset.

The bad news is that the first smoke version probably overshoots. For several key intermediates, the canonical augmented dataset is not just richer than the current training data — it is richer than the stock active CFD distribution we are trying to match.

So this is still progress. It means the local-paper-inspired path is real and powerful. The next problem is not whether canonical augmentation can create the missing chemistry, but how to calibrate it so that it helps instead of overdriving the model.
