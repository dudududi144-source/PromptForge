# PromptForge Architecture

## Overview

PromptForge is a production-grade system that combines AI code generation,
quality assurance, and automated deployment into a unified CLI.

## Architecture

    User -> Gateway -> [Nova | PromptForge | Forge] -> Deploy

## Components

| Component | Purpose |
|-----------|---------|
| Gateway | Entry point, auth, rate limiting |
| Nova Engine | Code generation |
| PromptForge | Code enhancement |
| Forge Engine | Deployment |
| Turso DB | Persistent storage |

## Design Decisions

1. **Supervisor Pattern**: Agents are one-level deep, no sub-agents
2. **WIP Limit**: Max 5 concurrent agents
3. **Kill Criteria**: 3+ iterations on same error = stop
4. **One File, One Owner**: Never two agents editing same file
5. **Quality Gates**: lint + type-check + tests must pass