# ReserV9 – Web-based Facility & Restaurant Booking

ReserV9 is a lightweight, modern web app for discovering facilities/restaurants and making quick bookings. It runs with a single command and uses a CSV dataset as its source of truth.

## How to Run
- Ensure Python 3.8+ is installed.
- In the project root, run: `python ReserV9.py`
- The app opens at `http://127.0.0.1:5000/` automatically.
- Optional custom port: `python ReserV9.py 8080`

## Features
- Interactive UI with search, rating badges, and cuisine filter chips.
- In-browser booking flow with toast feedback.
- Simple login verification (empty token maps to `guest`).
- Reads data from `onlinefoodbookings.csv` (auto-migrated from legacy file if needed).

## Tech Stack
- Backend: Python standard library (`http.server`, no external deps).
- Frontend: HTML + Tailwind CDN + vanilla JavaScript.
- Data: `onlinefoodbookings.csv` CSV file.

## API Endpoints
- `GET /api/restaurants` — returns dataset rows (ReserV9.py:144).
- `GET /api/auth/verify-login/<token>` — normalizes token (defaults to `guest`) and returns ok=true (ReserV9.py:153).
- `POST /api/book` — records in-memory booking for the session (ReserV9.py:158).

## Structure
- `ReserV9.py` — server entrypoint and routes.
- `templates/index.html` — main page.
- `static/js/app.js` — client-side interactivity.
- `onlinefoodbookings.csv` — dataset consumed by the server.

## Notes
- Bookings are stored in-memory; persistence requires a database.
- Legacy Node/TS files exist but are not used by the Python server.
