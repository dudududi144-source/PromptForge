# PromptForge

AI-powered code generation tool. Describe what you want to build, get working code in seconds.

## Features

- AI Code Generation (DeepSeek Coder, Llama 3.1)
- Dark/Light Mode
- Build History (last 10)
- 8 Templates
- Live HTML Preview
- Code Refine/Iterate
- Export (auto-detect language)
- Favorites
- Code Validation Hints
- Copy as Markdown
- Line Numbers Toggle
- Auto-save Draft
- Share Links
- Code Stats
- Keyboard Shortcuts

## URLs

- UI: https://promptforge-ui.pages.dev
- Worker: https://promptforge.rabotatony.workers.dev

## API Endpoints

- GET /api/health - Health check
- POST /api/plan - Generate action plan
- POST /api/build - Generate code
- POST /api/iterate - Refine existing code

## Setup

1. Get NVIDIA Build API key from https://build.nvidia.com
2. Open https://promptforge-ui.pages.dev
3. Settings -> Enter API key -> Save
4. Start building!

## Tech Stack

- Frontend: Vanilla HTML/CSS/JS
- Backend: Cloudflare Workers
- AI: NVIDIA Build API
- Hosting: Cloudflare Pages + Workers