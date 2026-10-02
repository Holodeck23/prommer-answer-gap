# Task 1 requirements

- [x] "Ship a multi-step agentic workflow for prommer.net."
- [x] Use "at least two distinct agent steps" rather than a single-prompt result.
- [x] Explain each trigger, tool, agent handoff, output, and data passed to the next step.
- [x] Provide a public link to the specific build.
- [x] Explain where the pipeline broke and exactly what changed to fix it.

## Internal acceptance gates

- [x] Measure the live site before designing the workflow.
- [x] Freeze the source corpus and preserve prompts, responses, timing, usage, and cost.
- [x] Separate drafting and verification roles, then use deterministic publish gates.
- [x] Provide a replay path that makes no model calls.
- [x] Run planted fake-statistic and fake-expert negative controls.
- [x] Preserve failed runs and document the fixes.
- [x] State limitations and reused tooling honestly.
