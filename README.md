# PromptForge

> Autonomous AI Software Development Orchestrator

PromptForge is a production-grade system that combines AI code generation,
quality assurance, and automated deployment into a unified CLI.

## Quick Start

    pip install -e ".[dev]"
    cp .env.example .env
    # Edit .env with your NVIDIA API key
    promptforge run "Build a REST API"

## Architecture

    User -> Gateway -> [Nova | PromptForge | Forge] -> Deploy

## Components

| Component | Purpose | Status |
|-----------|---------|--------|
| Gateway | Entry point, auth, rate limiting | Active |
| Nova Engine | Code generation | Active |
| PromptForge | Code enhancement | Active |
| Forge Engine | Deployment | Active |
| Turso DB | Persistent storage | Active |
| Chat UI | Frontend | Active |

## Deployment

### Cloudflare Workers
- Gateway: https://rabotatony.workers.dev/promptforge-gateway
- API: https://rabotatony.workers.dev/promptforge-api

### Cloudflare Pages
- Chat UI: https://promptforge-ui.pages.dev

## License

MIT
