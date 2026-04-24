# C2H4 priority reset: stop local mix-ratio hill-climbing for now and refocus on the real bottleneck—label semantics and deployment-facing diagnostics

_Date: 2026-04-24_

## Why I am resetting priorities

The recent C2H4 canonical-mix work was useful, but the last few steps made the marginal-return pattern clearer:
- `dp100 + canonical@0.1` was a real improvement
- `dp100 + canonical@0.2` improved further
- nearby ratio sweeps are informative, but each additional local point is now buying less understanding per unit time than earlier steps

So this is the right time to step back and re-rank the tasks.

## What the evidence now says

### 1) We already have a credible current-best C2H4 data-side baseline
The current best tested C2H4 mixed dataset path is:
- **`dp100 + canonical@0.2`**

That is good enough to serve as the present reference point for the next round of reasoning.

### 2) The main question is no longer “does calibrated canonical mixing help?”
That question is now answered well enough for current planning:
- **yes, it helps**
- and it helps more than raw dataset scaling alone in the current setup

### 3) The main unresolved bottleneck is deeper than mix ratio
The stronger remaining uncertainty is:
- **what target semantics are we actually teaching the model, and how does that mismatch show up in deployment?**

The present labels are still full-CFD state transitions, not isolated chemistry-only labels. That means:
- pressure and transport effects are entangled in the targets
- source-term behavior can be distorted even when the run remains numerically stable
- local dataset sweeps can move metrics around without resolving the deeper problem

## What to deprioritize now

### Deprioritize
- more fine-grained canonical mix-ratio hill-climbing as the main thread
- blind nearby sweeps whose main output is just another point on the same response curve

This does **not** mean the sweep results were wasted. They established the important qualitative fact that:
- calibrated canonical enrichment works
- the best region is above `0.1`
- the response is non-monotone

That is enough for now.

## What to prioritize now

### Priority 1: freeze a current-best C2H4 reference
Use:
- **`dp100 + canonical@0.2`**

as the current deployment-facing data baseline for C2H4 while the next diagnostics are built.

### Priority 2: run a deployment-facing error anatomy study
The next high-value question is not another mix point. It is:
- **why does the current best mixed model still differ from stock where it matters?**

Specifically, the next diagnostic should compare the best mixed C2H4 model against stock on matched active-case states and quantify:
- source-term sign and magnitude differences
- late intermediate/product suppression or overproduction
- thermodynamic drift patterns
- whether the dominant remaining error is concentrated in a specific regime window

### Priority 3: invest in better labels, not just better weighting
The longer-term C2H4 forward path should now focus on:
- chemistry-isolated or more chemistry-faithful relabeling
- canonical-state relabeling with clearer target semantics
- regime-targeted enrichment driven by diagnostic evidence, not just dataset mixing ratios

## Practical task ranking

### Highest-value next thread
1. **Build a best-model-vs-stock diagnostic around the current best mixed C2H4 baseline (`r=0.2`)**
   - explain the remaining error structure
   - identify whether source-term sign, specific species, or a regime boundary is the main residual problem

### Second
2. **Design the next label-improvement path**
   - use the diagnostic to decide where chemistry-only relabeling or stronger canonical relabeling would matter most

### Lower for now
3. further local mix-ratio sweeps

## Current decision

For the next phase, treat:
- **local canonical-mix sweep work as sufficiently explored for now**
- **`dp100 + canonical@0.2` as the current C2H4 data baseline**
- **deployment-facing diagnostic anatomy and label-semantics improvement as the main task**

## Immediate next step

The next concrete step should therefore be:
- build a targeted comparison script and finding that explains where the current best mixed C2H4 model still diverges from stock at `5e-6`, instead of adding more nearby mix points first.
