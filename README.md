# EatHub

EatHub is a multi-tenant ERP platform for restaurant and hospitality
operations. The repository contains a Django REST API, a React and TypeScript
web client, and Docker-based deployment configuration.

## Repository layout

- `backend/` — Django project and applications, including accounts, products,
  inventory, purchase, customer, financial, and shared core functionality.
- `frontend/` — React and TypeScript application built with Vite.
- `deployment/` — Docker Compose, Nginx, release, and static-asset integrity
  documentation and configuration.

The backend project settings are in `backend/EatHub/settings.py`. The Purchase
application uses domain, application, infrastructure, and presentation layers;
other backend applications may follow their existing Django conventions.

## Backend development

Use a Python version compatible with the packages in `backend/requirements.txt`.
From the repository root, create and activate a virtual environment, then
install the backend requirements:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Configure the backend environment and a local development database according
to `backend/EatHub/settings.py` before running Django management commands. Run
migrations only against the intended development database. To initialize and
start the local Django development server:

```powershell
python manage.py migrate
python manage.py runserver
```

Run backend tests from `backend/` with the configured interpreter:

```powershell
python manage.py test
```

Ensure the test database is isolated from persistent development data before
running tests.

## Frontend development

From `frontend/`, install the versions recorded in the npm lockfile and start
the Vite development server:

```sh
npm ci
npm run dev
```

The available validation scripts are:

```sh
npm run lint
npm run build
```

`deployment/.env.frontend.example` documents public frontend build settings.
Values exposed to the browser must not contain credentials or other secrets.
Keep real environment files and local configuration out of Git.

## Deployment

Review [deployment/STATIC_ASSETS.md](deployment/STATIC_ASSETS.md) for the
repository's documented release, rollback, and static-asset integrity process.
Deployment procedures have operational prerequisites; do not run them against
a live environment without the required review and authorization.
