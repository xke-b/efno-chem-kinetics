# Agent guidance

## Tasks
- Build a reliable workflow for reading technical papers from PDF and converting them into structured implementation notes.
- Extract a faithful implementation and evaluation spec for the EFNO stiff-chemistry paper from its PDF.
- Reproduce the paper incrementally on small benchmarks before attempting complex CFD-coupled cases.
- Evaluate generalization, rollout stability, and physical consistency under unseen conditions.
- Test whether EFNO improves CFD-coupled performance versus standard chemistry integration.
- Explore improvements only after a working reproduction baseline exists.
- Publish findings on the project docs site with code blocks, text, images, and figures, and write regular technical blog posts.
- If PDF understanding is a bottleneck, research and propose the smallest robust Pi extension or auxiliary multimodal/document-ingestion pipeline.

## Guidelines
- Reproduce before modifying.
- Record PDF ambiguities, assumptions, and deviations explicitly.
- Prefer small, reproducible experiments before expensive simulations.
- Optimize for coupled-simulation usefulness, not only offline ML accuracy.
- Use the docs site as the default public record of results, decisions, and experiment evidence.
- Research existing tools and Pi capabilities before adding new extensions.
