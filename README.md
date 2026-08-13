# PromptForge

Task to working code in seconds.

## Live

- UI: https://promptforge-ui.pages.dev
- Worker: https://promptforge.rabotatony.workers.dev

## Features

- ONE field, ONE button
- 4-bar progress indicator
- Code display + Live preview
- Inline iterate
- 10 templates
- History, Stats, Plans, Favorites tabs
- Share, Notes, Compare
- Health indicator
- Help modal
- Font size adjustment
- Export history as JSON
- Retry on error
- Recent tasks

## API

- POST /api/plan - Analyze task
- POST /api/build - Generate code
- POST /api/iterate - Fix code
- GET /api/health - Status

## Stack

- Frontend: Vanilla HTML/CSS/JS
- Backend: Cloudflare Worker
- AI: NVIDIA Build API
- Hosting: Cloudflare Pages + Workers

## Changelog

### v1.0 Final
- ONE worker with 4 endpoints
- ONE screen UI with clean design
- 10 templates
- History, Stats, Plans, Favorites
- Share, Notes, Compare
- Health indicator + Help modal
- Font size + URL task loading
- Export + Retry + Recent tasks
- Meta tags + Favicon + CI/CD

## License

MIT