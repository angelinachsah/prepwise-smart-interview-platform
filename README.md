# Prepwise — Smart Interview Preparation Platform

Prepwise is a local Flask application for placement and interview preparation. It brings a categorized question bank, timed multiple-choice mock tests, beginner coding exercises, HR answer drafts, progress summaries, and rule-based next-step recommendations into one responsive student workspace.

## Project overview

Students often prepare from scattered materials and have difficulty seeing which subjects need more attention. Prepwise provides one place to practice and review measurable activity. Administrators can create learning questions and mock tests and review submitted test results.

### Features

- Session-based registration, login, logout, hashed passwords, role checks, CSRF protection, and profile/password updates.
- Student dashboard with database-backed counters, recent activity, and a subject performance chart.
- Searchable, filterable, paginated question bank with bookmarks, multiple-choice practice, and explanations.
- Timed mock tests with server timestamps, answer validation, server-side scoring, one-time submission, and private result pages.
- Fifteen beginner coding prompts. The server stores submissions and checks a manually entered sample output; it never executes submitted code.
- Twenty HR prompts with saved drafts, example structures, and a practice checklist.
- Performance summaries and transparent rule-based recommendations that are refreshed after practice/test activity.
- Admin tools for managing categories, creating/editing questions, creating/configuring mock tests, adding coding and HR content, enabling/disabling student accounts, and reviewing student accounts and submitted test results. Content with saved attempt history is protected from destructive edits.
- Responsive layouts, reduced-motion support, Chart.js visualizations, and an optional mouse-following color halo with gentle hover vibration on pointer-capable devices.

## Technology

- Python 3.12+ (tested with Python 3.14)
- Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, SQLite
- HTML5, CSS, JavaScript, Chart.js
- pytest

## Project layout

```text
.
├── app.py                 # Application factory and routes
├── config.py              # Environment-based configuration
├── models.py              # SQLAlchemy data models
├── seed.py                # Idempotent sample-data and admin setup
├── run.py                 # Development entry point
├── requirements.txt
├── templates/             # Jinja pages
├── static/css/style.css
├── static/js/app.js
├── tests/test_app.py
└── docs/
    ├── SRS.md
    ├── TEST_CASES.md
    └── diagrams/*.puml
```

## Setup on Windows

Open PowerShell in this project folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env`. Set a long random `FLASK_SECRET_KEY`, `ADMIN_EMAIL`, and a unique `ADMIN_PASSWORD` (at least eight characters with upper/lowercase letters and a number). Then initialize and seed:

```powershell
python seed.py
python run.py
```

The local app will be available at `http://127.0.0.1:5000`.

For a disposable local demo only, the seed command supports a development account:

```powershell
python seed.py --demo
```

This prints `admin@example.com / DemoAdmin2026!`. Do not use this demo password outside an isolated local demonstration. It is not the default production credential. To reset all local database content and reseed it, run `python seed.py --reset`; this deletes the configured database contents.

## Setup on Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Set FLASK_SECRET_KEY, ADMIN_EMAIL, and ADMIN_PASSWORD in .env.
python seed.py
python run.py
```

## Environment variables

| Variable | Purpose |
|---|---|
| `FLASK_SECRET_KEY` | Session signing and CSRF secret. Set a random private value. |
| `DATABASE_URL` | SQLAlchemy URL; defaults to a SQLite file. |
| `ADMIN_EMAIL` | Admin account email created by `seed.py`. |
| `ADMIN_PASSWORD` | Admin password; always stored as a Werkzeug hash. |
| `COOKIE_SECURE` | Set to `1` only when serving HTTPS. |

`create_app()` creates database tables on startup. Run `seed.py` to load sample learning data. Seeding is repeatable and avoids duplicate sample records.

## Testing

Run the automated tests from the project root:

```powershell
python -m pytest -q
```

Tests use isolated temporary SQLite databases and do not alter the local demo database. The test case catalog in [docs/TEST_CASES.md](docs/TEST_CASES.md) includes manual cases marked Pending until genuinely executed.

## Documentation and UML

- [Software Requirements Specification](docs/SRS.md)
- [Detailed test case catalog](docs/TEST_CASES.md)
- Five PlantUML source diagrams are in `docs/diagrams/`. Render them with a local PlantUML installation, for example `plantuml docs/diagrams/*.puml`.

## Screenshots

No screenshots are included yet. Start the app and capture the landing page, student dashboard, test/result, and admin workspace for an evaluation presentation.

## Security notes and limitations

- Change the development-only fallback secret before deployment; provide `FLASK_SECRET_KEY` through the environment.
- Use HTTPS and set `COOKIE_SECURE=1` when deployed behind TLS. This application is intended for local student demonstrations, not as-is production hosting.
- CSRF protection is enabled for forms; passwords use Werkzeug's password hashing; student/admin authorization is enforced in routes.
- Test correct answers are never included in the test-taking page, and grading happens on the server. Attempts are owner-only.
- Coding submissions are stored and compared only against a displayed sample output manually entered by the student. The server does **not** execute code, evaluate expressions, or claim hidden-test acceptance.
- Chart.js and web fonts are loaded from public CDNs; an internet connection is needed for those assets. Core forms, navigation, and server routes remain local.
- SQLite is suitable for the single-process demonstration. Production deployment needs hardened configuration, backups, migrations, monitoring, rate limiting, and a production WSGI server.
- Recommendation rules are transparent score bands, not machine learning. Scores are omitted until real activity is recorded.

## Future enhancements

Add database migrations, richer admin CRUD/content editing, optional isolated code execution, accessible downloadable reports, date/category analytics filters, and integrations only when configured and privacy reviewed.
