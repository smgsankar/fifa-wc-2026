# WC26 Predictor — Frontend

A responsive dashboard for World Cup 2026 match predictions: the next match with a live countdown, model performance stats, full fixtures & results, and per-match detail (prediction, head-to-head, recent form, squads). Light/dark theme with an editorial, match-day-broadsheet look.

Built with **Vite + React 19 (TypeScript) + TailwindCSS v4 + react-router 7**. Deploys to **Cloudflare Pages**.

## Pages

| Route | Description |
|---|---|
| `/` | Hero card for the next match (countdown, win probabilities, confidence), next 3 matches, model stats |
| `/matches/:match_id` | Full match detail: prediction verdict, H2H, last-5 form per team, squads, actual score when completed |
| `/fixtures` | All tournament matches with URL-synced filters (status / team / stage / date) and sorting (date, team, prediction accuracy) |
| anything else | 404 |

## Local setup

Prerequisites: Node ≥ 20.

```bash
npm install
cp .env.example .env.local   # then point it at your backend
npm run dev                  # http://localhost:5173
```

### Environment variables

| Variable | Required | Notes |
|---|---|---|
| `VITE_API_BASE_URL` | yes | Backend base URL, no trailing slash (e.g. `http://localhost:8000`). **Build-time** — baked into the bundle by Vite; changing it requires a rebuild/redeploy. |

If the backend is unreachable, every section degrades to an error card with a Retry button — the app itself still loads.

### Scripts

| Script | Purpose |
|---|---|
| `npm run dev` | Dev server with HMR |
| `npm run build` | Type-check + production build to `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | ESLint |

## API endpoints consumed

- `GET /api/matches/next-4` — home page hero + next-3 cards
- `GET /api/matches/:match_id` — match detail
- `GET /api/matches/all` — fixtures page (filtering/sorting is client-side)
- `GET /api/model/stats` — model performance section

Response shapes are defined in the backend PRD (`../backend/prd.md`) and mirrored in [`src/lib/types.ts`](src/lib/types.ts).

## Project structure

```
src/
├── lib/        types.ts (API contract), api.ts (fetch wrapper + endpoints), format.ts
├── hooks/      useFetch, useCountdown, useTheme
├── components/
│   ├── layout/    app shell, navbar, theme toggle
│   ├── ui/        badges, skeletons, error/empty states, team logo with fallback
│   ├── match/     hero card, compact card, probability bar, countdown
│   ├── stats/     model stats section
│   ├── detail/    match header, prediction panel, H2H, form, squads
│   └── fixtures/  filter controls, fixture row
└── pages/      Home, MatchDetail, Fixtures, NotFound
```

## Theming

Dark mode uses Tailwind's class strategy: an inline script in `index.html` applies `.dark` before first paint (no flash), preference persists in `localStorage` and defaults to the system `prefers-color-scheme`.

## Deploying to Cloudflare Pages

Create a Pages project from this repo with:

| Setting | Value |
|---|---|
| Root directory | `frontend` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Environment variable | `VITE_API_BASE_URL=https://<your-backend>.railway.app` (Production **and** Preview) |

`public/_redirects` (`/* /index.html 200`) is copied into `dist/` so SPA deep links like `/matches/12` survive refresh. Remember: changing the backend URL requires a redeploy since the env var is build-time.
