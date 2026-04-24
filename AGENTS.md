# Guidance

## Tasks
- Build a reliable workflow for reading technical papers from PDF and converting them into structured implementation notes.
- Extract a faithful implementation and evaluation spec for the EFNO stiff-chemistry paper from its PDF.
- Reproduce the paper incrementally on small benchmarks before attempting complex CFD-coupled cases.
- Reframe the current program around the concrete end goal of a full implementation study of **EFNO applied to H2 and C2H4 surrogate chemistry in CFD**, including both offline reproduction and coupled DeepFlame evidence.
- Evaluate generalization, rollout stability, and physical consistency under unseen conditions.
- Test whether EFNO improves CFD-coupled performance versus standard chemistry integration.
- Integrate and test learned models in the two CFD cases under `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame`.
- For H2 and C2H4, prioritize work that closes the gap between current partial results and a defensible end-to-end implementation/deployment story rather than open-ended local tuning.
- Explore improvements only after a working reproduction baseline exists.
- Publish findings on the project docs site with code blocks, text, images, and figures, and write regular technical blog posts.
- Treat manuscript preparation as an active parallel workstream: keep converting validated results into figures, tables, sections, and explicit claim boundaries for a reviewable paper.
- Produce final results as a LaTeX manuscript with sufficient detail, figures, results, and discussion to form an academic preprint on EFNO for H2 and C2H4 surrogate chemistry in CFD, and compile it to PDF for peer review.
- When running DeepFlame cases with an integrated neural-network chemistry model, default to GPU inference whenever the environment supports it; consult related DeepFlame examples in `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch` for the expected `TorchSettings` / inference configuration pattern before deviating.
- If PDF understanding is a bottleneck, research and propose the smallest robust Pi extension or auxiliary multimodal/document-ingestion pipeline.

## References and paths
- Papers directory: `/root/workspace/papers`
- EFNO paper PDF: `/root/workspace/papers/Weng et al. - 2025 - Extended Fourier Neural Operators to learn stiff c.pdf`
- OpenFOAM root: `/opt/openfoam7`
- DeepFlame repo: `/opt/src/deepflame-dev`
- DFODE-kit repo: `/opt/src/DFODE-kit`
- DFODE-kit GitHub: `https://github.com/xke-b/DFODE-kit`

## Guidelines
- Reproduce before modifying.
- Record PDF ambiguities, assumptions, and deviations explicitly.
- Prefer small, reproducible experiments before expensive simulations.
- Optimize for coupled-simulation usefulness, not only offline ML accuracy.
- Use the docs site as the default public record of results, decisions, experiment evidence, and organized technical notes.
- Use Python plotting/imaging tools such as `matplotlib` to generate figures, images, and scalar-field/contour visualizations for experiments and simulations whenever they help communicate results, failure modes, comparisons, or conclusions more clearly.
- Write and organize docs continuously, not only at the end.
- Write technical blog posts regularly as work progresses, with more frequent updates than before; many people are following the work and expect a steady public record of progress.
- Treat the manuscript as a living deliverable, not an end-stage afterthought: whenever enough evidence exists, update the LaTeX draft, stabilize section claims, and turn key findings into manuscript-ready figures and tables.
- Prefer work that increases end-to-end paper readiness for the target study "EFNO applied to H2 and C2H4 surrogate chemistry in CFD": implementation fidelity, deployment evidence, negative results, and clear claim boundaries are all valuable.
- When choosing between nearby tuning sweeps and a task that strengthens the final implementation story or manuscript evidence chain, prefer the latter unless the sweep clearly resolves a major uncertainty.
- Treat use of the `exa-search` skill for web search and broader information exposure as a high-priority action whenever external documentation, code references, or current scientific context could reduce uncertainty.
- Carefully examine the other papers in `/root/workspace/papers` and reference them where they inform implementation choices, benchmark design, evaluation criteria, data workflows, or coupled-CFD relevance.
- Learn from the papers in `/root/workspace/papers` about task-relevant aspects of deep learning for chemical kinetics in CFD, including training dataset construction, sampling strategy, data augmentation, preprocessing, target formulation, postprocessing, physical constraints, rollout evaluation, and coupled-simulation validation.
- Use web search and scholarly APIs when useful to expand the reference graph; this can include searching for additional related papers or using APIs such as OpenAlex to gather cited, citing, or otherwise connected papers.
- Install and use a LaTeX toolchain when needed so the manuscript can be compiled to PDF locally before external review.
- Commit and push to the GitHub repo regularly using conventional commit messages such as `feat:`, `fix:`, and `docs:`; do this more frequently than before so progress does not sit uncommitted for long, and push to the remote more regularly as well instead of letting local commits accumulate.
- DFODE-kit is still under development; you are encouraged to extend, fix, and develop its code base, and commit or push changes to its `origin/main` at `https://github.com/xke-b/DFODE-kit` when appropriate.
- You are encouraged to write reusable assets such as scripts, utilities, templates, or Pi skills when they make the work more reliable, efficient, or reproducible.
- Research existing tools and Pi capabilities before adding new extensions.
