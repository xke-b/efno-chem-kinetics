# Guidance

## Tasks
- Build a reliable workflow for reading technical papers from PDF and converting them into structured implementation notes.
- Extract a faithful implementation and evaluation spec for the EFNO stiff-chemistry paper from its PDF.
- Reproduce the paper incrementally on small benchmarks before attempting complex CFD-coupled cases.
- Evaluate generalization, rollout stability, and physical consistency under unseen conditions.
- Test whether EFNO improves CFD-coupled performance versus standard chemistry integration.
- Integrate and test learned models in the two CFD cases under `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch/twoD_HIT_flame`.
- Explore improvements only after a working reproduction baseline exists.
- Publish findings on the project docs site with code blocks, text, images, and figures, and write regular technical blog posts.
- When running DeepFlame cases with an integrated neural-network chemistry model, default to GPU inference whenever the environment supports it; consult related DeepFlame examples in `/opt/src/deepflame-dev/examples/dfLowMachFoam/pytorch` for the expected `TorchSettings` / inference configuration pattern before deviating.
- Produce final results as a LaTeX manuscript with sufficient detail, figures, results, and discussion to form an academic preprint, and compile it to PDF.
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
- Write and organize docs continuously, not only at the end.
- Write technical blog posts regularly as work progresses, with more frequent updates than before; many people are following the work and expect a steady public record of progress.
- Treat use of the `exa-search` skill for web search and broader information exposure as a high-priority action whenever external documentation, code references, or current scientific context could reduce uncertainty.
- Carefully examine the other papers in `/root/workspace/papers` and reference them where they inform implementation choices, benchmark design, evaluation criteria, data workflows, or coupled-CFD relevance.
- Learn from the papers in `/root/workspace/papers` about task-relevant aspects of deep learning for chemical kinetics in CFD, including training dataset construction, sampling strategy, data augmentation, preprocessing, target formulation, postprocessing, physical constraints, rollout evaluation, and coupled-simulation validation.
- Use web search and scholarly APIs when useful to expand the reference graph; this can include searching for additional related papers or using APIs such as OpenAlex to gather cited, citing, or otherwise connected papers.
- Commit and push to the GitHub repo regularly using conventional commit messages such as `feat:`, `fix:`, and `docs:`; do this more frequently than before so progress does not sit uncommitted for long.
- DFODE-kit is still under development; you are encouraged to extend, fix, and develop its code base, and commit or push changes to its `origin/main` at `https://github.com/xke-b/DFODE-kit` when appropriate.
- You are encouraged to write reusable assets such as scripts, utilities, templates, or Pi skills when they make the work more reliable, efficient, or reproducible.
- Research existing tools and Pi capabilities before adding new extensions.
