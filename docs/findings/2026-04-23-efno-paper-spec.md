# EFNO paper implementation specification

_Date: 2026-04-23_
_Paper: Weng et al., "Extended Fourier Neural Operators to learn stiff chemical kinetics under unseen conditions"_
_Source PDF: `/root/workspace/papers/Weng et al. - 2025 - Extended Fourier Neural Operators to learn stiff c.pdf`_
_Extracted text artifacts: `/root/workspace/artifacts/papers/efno_weng_2025/`_

## Purpose of this note

This note captures the paper as an implementation contract for reproduction work. It separates:
- explicit facts from the paper text
- inferred implementation decisions
- unresolved ambiguities that must be tracked during reproduction

## High-level method summary

The paper extends FNO for stiff chemistry by combining:
1. **FNO backbone** to learn the one-step propagator
2. **Box-Cox transformation (BCT)** to regularize skewed species distributions
3. **physics-informed constraints** in training loss
   - element conservation
   - mass-fraction-sum conservation
4. **balanced / weighted loss** to address spatial or sample imbalance in complex reacting flows
5. **autoregressive rollout** where each prediction becomes the next input

## Core prediction target

The learned map is a one-step propagator:
- input: thermochemical state at time `t`
- output: thermochemical state at time `t + Δt` or the increment needed to recover it
- evaluation: recursive rollout over many steps

The paper repeatedly evaluates the model in **autoregressive mode**, not just single-step inference.

## Method details explicitly stated in the paper

### FNO / EFNO structure
- EFNO uses an encoder `P`, a stack of Fourier layers, and a decoder `Q`.
- Each Fourier layer has two paths:
  - linear transformation path
  - Fourier path: Fourier transform -> linear transform -> inverse Fourier transform
- The two paths are added in a residual-like fashion.
- Input is transformed with BCT before modeling.
- Output is inverse-transformed back to original space.

### Box-Cox transformation
Paper formula:
- `F(x) = (x^λ - 1) / λ` for `λ != 0`
- `F(x) = log(x)` for `λ = 0`

Paper motivation:
- chemistry species values can be very small
- BCT avoids singular behavior near zero that pure log transforms can suffer from
- BCT helps move values toward `O(1)` scale

### Physics-informed constraints
The paper defines total loss as:
- `L = λ1 * L_data + λ2 * L_elements + λ3 * L_mass_fraction`

Constraint terms described:
- `L_elements`: preserve element mole fractions before/after reaction
- `L_mass_fraction`: enforce sum of mass fractions equals 1

### Balanced loss / weighting
The paper first discusses focal loss motivation, then describes a practical weighting scheme based on adjacent mass-fraction variation `Δy` between consecutive snapshots.

Final weighted loss form in the text:
- `L_wl = (1/n) * sum β_i * (y_pred - y_true)^2`

Weight assignment:
- `β = 1` when `Δy > Q3`
- `β = 0.1` when `Δy < Q1 - IQR`
- `β = 0.5` otherwise

Important interpretation note:
- although Eq. (20) gives the focal-loss expression, Eqs. (21)-(22) look like the operative loss actually used in experiments for imbalanced reacting-flow data.
- reproduction should treat this as an ambiguity to test explicitly.

### Activation functions reported
- DNN baseline: Leaky ReLU
- POLLU and H2 autoignition EFNO: 4 Fourier blocks, Leaky ReLU
- 3D H2/NH3 turbulent jet flame EFNO: 6 Fourier blocks, Leaky ReLU

### Benchmark details stated in text

#### ROBER
- 3 species
- reaction constants: `k1 = 0.04`, `k2 = 3e7`, `k3 = 1e4`
- 12,000 random initial conditions
- train/test split: 80/20
- integration up to `t = 10^2 s`
- training time step: `Δt = 1e-5 s`
- test ranges extend beyond train ranges for `y1` and `y3`
- architecture study table compares 2/3/4/5 Fourier blocks
- best test error reported at 3 Fourier blocks for ROBER

#### POLLU
- 20 species, 25 reactions
- representative unseen-condition ranges extend for species `y1`, `y4`, `y17`
- EFNO used here: 4 Fourier blocks + Leaky ReLU
- recursive rollout used for evaluation

#### H2 autoignition
- H2/O2 mechanism with 7 species and 16 reactions
- 5000 initial conditions
- equivalence ratio range: `0.5 <= φ <= 2`
- train temperature range: `1200 <= T <= 1500 K`
- test temperature range: `1200 <= T <= 1600 K`
- each case integrated for 1000 steps
- step size: `Δt = 0.1 μs = 1e-7 s`
- approx. 2,000,000 paired samples generated
- evaluation also uses 100 additional distinct initial conditions
- comparisons shown against DNN, DeepONet, FNO/EFNO ablations
- BCT and physics-constraint ablations are reported

#### 3D H2/NH3 turbulent jet flame
- 24 species, 103 reactions
- mechanism derived from a CH4/NH3 mechanism by removing carbon-containing species
- LES baseline with Smagorinsky SGS and PaSR combustion interaction
- bulk injection velocity: `8.5 m/s`
- air coflow: `0.24 m/s`
- fuel composition by mole: `75.4% NH3`, `18.4% H2`, `6.2% N2`
- Reynolds number: `11200`
- `T = 298.5 K`, `p = 5 bar`
- about `2.6 million` cells
- 4000 LES time steps collected after statistical stationarity
- LES collection step size: `1e-6 s`
- training/eval snapshots:
  - `t1 = t0 + 250Δt`
  - `t2 = t0 + 500Δt`
  - `t3 = t0 + 750Δt`
  - `t4 = t0 + 1000Δt`
  - `t5 = t0 + 1250Δt`
- training inputs: `t0, t1, t2, t3`
- training outputs: `t1, t2, t3, t4`
- evaluation target: `t5`
- recursive rollout to `t1..t5` is also tested
- alternate rollout strategy tested:
  - recursively update species with EFNO
  - derive temperature from the high-fidelity solver / energy equation
- paper reports this reduces drift
- cross-Re test shown at `Re = 15000`

## Evaluation dimensions we should reproduce

1. **single-step accuracy**
2. **autoregressive rollout quality**
3. **unseen-condition generalization**
4. **physical consistency**
   - element conservation
   - mass-fraction sum
5. **ablation effects**
   - with/without BCT
   - with/without physics-informed constraints
   - with/without balanced loss
6. **cross-condition transfer**
   - outside train ranges
   - different Reynolds number for turbulent case

## Observed implementation ambiguities

### Ambiguity 1: exact FNO hyperparameters
Not clearly specified in extracted text:
- number of retained Fourier modes
- channel width / hidden width
- normalization layers, if any
- dropout, if any
- exact decoder/encoder widths

### Ambiguity 2: exact target parameterization
Paper text frames EFNO as predicting temporal evolution, but does not fully disambiguate whether the network predicts:
- next full state directly, or
- state increment in transformed space

For reproduction, both should be tested. Existing DeepFlame DNN examples use transformed delta prediction, which may be a useful baseline but should not be silently assumed to match paper EFNO.

### Ambiguity 3: exact loss coefficients
The paper writes `λ1`, `λ2`, `λ3` but the extracted text does not reveal actual numeric values.

### Ambiguity 4: optimizer/training schedule
Not clearly specified in extracted text:
- optimizer type
- learning rate
- scheduler
- batch size
- epochs / early stopping

### Ambiguity 5: weighted-loss implementation granularity
Unclear whether `β` is:
- per scalar component
- per grid point
- per species-grid sample
- aggregated across species at a point

### Ambiguity 6: H2 temperature-range typo possibility
One extracted passage says the test dataset includes `1000 <= T <= 1600`, but Table 4 clearly shows `1200 <= T <= 1600`. Table values should be treated as primary until contradicted.

## Reproduction assumptions to adopt initially

Unless contradicted by later evidence, start with:
1. Table values override surrounding prose when inconsistent.
2. For H2 autoignition, use `T_train = [1200,1500] K`, `T_test = [1200,1600] K`.
3. Use autoregressive rollout as the primary evaluation mode.
4. Implement both:
   - vanilla FNO baseline
   - EFNO = FNO + BCT + physical losses + weighted loss
5. Treat weighted quartile loss as the primary balanced-loss interpretation.
6. Record all missing hyperparameters as explicit reproduction degrees of freedom.

## Concrete reproduction order

1. ROBER with minimal EFNO/FNO implementation
2. POLLU with same code path
3. H2 autoignition with Cantera-generated paired data
4. deepened evaluation of rollout/generalization/physics consistency
5. DeepFlame-coupled adaptation to target cases

## Artifact links

- Extraction script: `/root/workspace/scripts/extract_pdf_text.py`
- Extraction report: `/root/workspace/artifacts/papers/efno_weng_2025/extraction_report.md`
- Full extracted text: `/root/workspace/artifacts/papers/efno_weng_2025/full_text.txt`

## Open follow-up tasks

- [ ] inspect references or supplementary sources for missing EFNO hyperparameters
- [ ] search for public code or author repositories
- [ ] decide initial FNO implementation backend
- [ ] map paper H2 benchmark onto DFODE-kit data/training APIs
- [ ] design physical-consistency metrics for rollout evaluation
