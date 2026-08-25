# Darul Taqwa Student Management System

A production-oriented monorepo for managing students at a Quran memorisation institution. The React application consumes a Django REST API; authorization is enforced by the API.

## Features

- JWT login, refresh, logout/blacklisting, current user, and protected role-aware routes
- Student enrolment, search, filters, pagination, soft deactivation, profiles, guardians, teacher assignment, and notes
- Controlled 114-surah catalogue and validated Hifz progress (Surah, Juz, percentage, dates, revision)
- Unique daily attendance with bulk recording endpoint, filters, date ranges, and dashboard statistics
- Admin teacher management; teacher querysets are restricted to assigned students
- Role-specific dashboard summaries, audit records, consistent API errors, OpenAPI schema and Swagger UI
- Responsive React interface with reusable controls, loading, error, and empty states

## Architecture

`frontend/` is a Vite + React + TypeScript SPA. `backend/` is Django + DRF split into `accounts`, `teachers`, `students`, `hifz`, `attendance`, `audit`, and `dashboard` apps. MySQL is configured with the `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` environment variables; Django ORM constraints preserve history and integrity.

## Setup

Requirements: Python 3.11+, Node 20+, MySQL 8.0+.

```powershell
Copy-Item .env.example .env
# Create the MySQL database/user, then set the DB_* values in .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
cd backend
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

The UI runs at `http://localhost:5173`. API docs are at `http://localhost:8000/api/docs/`; the schema is `/api/schema/`.

## API overview

- Auth: `/api/auth/login/`, `refresh/`, `logout/`, `me/`
- Students: `/api/students/`, `/{id}/`, `/{id}/deactivate/`, `/notes/`
- Hifz: `/api/hifz/`, `/api/hifz/surahs/`
- Attendance: `/api/attendance/`, `/api/attendance/bulk/`
- Teachers: `/api/teachers/`
- Dashboards: `/api/dashboard/admin/`, `/api/dashboard/teacher/`
- Audit: `/api/audit/` (admin only)

## Tests and production

```powershell
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
cd ..\frontend
npm run lint
npm run build
```

For deployment set `DEBUG=False`, a random `SECRET_KEY`, exact allowed hosts/origins, TLS, and a managed MySQL URL. Serve the frontend `dist/` via a CDN/web server and run Django behind a production WSGI/ASGI server. Never commit `.env`.
