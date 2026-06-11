# FRONTEND (Vite + React)

**Project: World Cup 2026 Prediction Dashboard**
**Deployment: Cloudflare Pages**
**Tech Stack: Vite, React, TailwindCSS**


## Scope

Build a responsive web app that displays World Cup match predictions. Consumes backend API and displays data beautifully.

## Features

1. Home/Landing Page

Primary Match Section:
- Display next upcoming match (biggest, most prominent)
- Show team names, logos, match date
- Show prediction: win probabilities + confidence
- Show countdown timer to match


Next 3 Matches Section:
- Compact cards for next 3 upcoming matches
- Show team names, logos, prediction
- Clickable (navigates to match detail)


Model Stats Section:
- Display global accuracy, precision, recall
- Show total predictions, correct predictions, win rate
- Simple stats cards/bars

2. Match Detail Page

**URL: /matches/:match_id**

- Show full match info (teams, date, stage)
- Recent Form Section: Last 5 matches for each team (opponent, result, score)
- H2H Section: Head-to-head history (wins, draws, losses, last match)
- Squad Section: Full squad rosters (players, positions, numbers)
- Prediction Section: Show our prediction + confidence
- Result Section (if match completed): Actual score + whether prediction was correct

3. All Fixtures & Results Page

**URL: /fixtures**

- Display all 64 tournament matches
- Filter options: By date, by team, by status (completed/pending)
- For completed matches: Show actual score + our prediction + ✓/✗ indicator
- For pending matches: Show our prediction
- Sortable by date, team, accuracy


## Pages

1. Home (/)
2. Match Detail (/matches/:match_id)
3. All Fixtures (/fixtures)
4. 404 page


## Technical Requirements

- Use Vite for fast dev/build
- Use React hooks (useState, useEffect)
- Fetch from backend API (CORS should work)
- Responsive design (mobile + desktop)
- Error handling (loading states, error messages)
- No authentication needed


## API Integration

### Consume backend endpoints:

- GET /api/matches/next-4 → Home page
- GET /api/matches/:match_id → Match detail
- GET /api/matches/all → All fixtures
- GET /api/model/stats → Model stats card

## Styling

- Use TailwindCSS
- Mobile-responsive
- Clean, modern design
- Color scheme: Professional football theme

## Deliverables

✅ Vite + React app with all 3 pages
✅ Components for match cards, team info, stats
✅ API integration (all endpoints working)
✅ Setup to deploy to Cloudflare Pages
✅ Responsive design (mobile + desktop)
✅ README with setup instructions


## Success Criteria

1. Homepage displays correctly
2. Can click matches → detail page loads
3. All fixtures page shows all matches
4. Data from backend API displays correctly
5. Mobile responsive
6. Deployed and publicly accessible

