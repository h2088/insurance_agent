# Insurance Agent

This repository contains a multi-agent insurance assistant prototype built around:

- an orchestrator agent
- four domain subagents (`health`, `auto`, `home`, `life`)
- tool-based workflows for quoting, eligibility, claims, and policy purchase
- markdown-based skills
- conversation compression
- structured and episodic memory
- LangSmith tracing

## What This Project Demonstrates

The project is designed as an agent engineering experiment rather than a production insurance system. It explores:

- orchestrator + subagent delegation
- tool scoping for domain isolation
- skill loading from markdown files
- memory write / retrieve loops
- context compression for long conversations
- trace-based evaluation and debugging

## Repository Structure

- `insurance_subagent_loop_with_skill.py`: main orchestrator, subagent loop, memory, compression, tracing
- `insurance_agent_tools_extended.py`: mock tool catalog and execution layer
- `*.md`: orchestrator and specialist skills
- `memory/`: structured and episodic memory snapshots generated during runs
- `logs/`: saved conversation logs generated during runs

## Important Data Notice

All business data in this repository is synthetic and for demonstration only.

This includes:

- insurance product data
- customer profiles
- claim records
- conversation logs
- structured memory
- episodic memory

These records are mock / LLM-created runtime artifacts and do **not** represent real customers, real policies, or real insurer data.

## Notes

- The `logs/` and `memory/` folders are intentionally included in this repository so the full agent workflow can be inspected.
- The included files show how the agent writes case state, retrieves memory, and stores prior conversations across runs.
