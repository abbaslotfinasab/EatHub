# EatHub staging deployment

This is a separate, disposable environment for browser-based acceptance tests.
It must never connect to production databases, storage, secrets, or domains.

## Architecture

- Frontend: Cloudflare Pages, connected to this repository.
- Cloudflare Workers Builds are intentionally disconnected for this staging slice. The frontend is deployed by Pages and the API by Render; no Worker build/deploy is part of this architecture. Do not recreate a Workers Build connection for this repository unless a real Worker service is introduced with its own checked-in Wrangler configuration.
- API: Render Docker Web Service defined in the root `render.yaml`.
- Database: a dedicated PostgreSQL project on Neon (not Render's expiring
  free PostgreSQL instance).
- Uploads: local Django media storage is temporary on Render Free. Do not treat
  uploaded files as durable; configure an S3-compatible object store such as
  Cloudflare R2 before testing workflows that need persistent uploaded assets.
- Celery/Redis: no worker is deployed in the first staging slice. The current
  repository deployment notes state that application business tasks are not
  implemented. Add a separate broker and worker only when a real task requires
  them.

## Create the services

### 1. PostgreSQL on Neon

Create a new Neon project named for staging, in a region close to Render
Frankfurt. Do not reuse a production database or copy production personal data.
Copy the pooled or direct PostgreSQL connection string into Render as
`DATABASE_URL`. The staging settings enforce TLS with `sslmode=require`
unless the URL explicitly provides another sslmode.

Neon's Free plan has limited compute hours and 1 GB storage per project;
compute scales to zero after inactivity. Check the provider's current quotas
before relying on it for longer test sessions.

### 2. Render API

Connect the GitHub repository to Render and create a Blueprint using the root
`render.yaml`. Select the branch `chore/staging-deployment-foundation` for
the initial review, then use the reviewed default branch after the PR is merged.

Set the following values in the Render service environment:

- `SECRET_KEY`: a newly generated, staging-only Django secret.
- `DATABASE_URL`: the staging-only Neon connection string.
- `CORS_ALLOWED_ORIGINS`: the exact Cloudflare Pages origin, for example
  `https://<project>.pages.dev`.
- `CSRF_TRUSTED_ORIGINS`: the same exact HTTPS frontend origin.

Render provides `RENDER_EXTERNAL_HOSTNAME` at runtime; the staging settings
include it in Django's allowed hosts. Do not add wildcard hosts or wildcard
CORS origins.

The service runs migrations at startup and then starts Gunicorn. It uses one
worker to stay within the Free instance's memory budget. Render Free web
services sleep after 15 minutes without inbound traffic and can take about a
minute to wake. Their local filesystem is ephemeral and is lost on restart,
redeploy, or sleep. This is suitable only for disposable staging data.

### 3. Cloudflare Pages frontend

Create a Pages project from the same GitHub repository:

- Production branch: `main` after the staging PR has been reviewed and merged.
- Root directory: `frontend`.
- Build command: `npm ci && npm run build`.
- Build output directory: `dist`.
- Node.js version: `22`.

Set these Pages environment variables for the production deployment:

- `VITE_API_BASE_URL`: `https://<render-service>.onrender.com/api`.
- `VITE_BASE_URL`: `https://<project>.pages.dev`.

The `frontend/public/_redirects` file provides SPA fallback for React Router
routes such as `/purchase/orders`. Configure the exact Pages origin in the
Render CORS and CSRF environment variables after the first Pages deployment.
If the Pages project uses preview deployments, add only the specific preview
origins that are intentionally trusted.

## First smoke test

1. Confirm the API root responds over HTTPS and the Render service can connect
   to the staging Neon database.
2. Confirm Django migrations complete successfully.
3. Confirm the frontend loads and a direct refresh of `/login`,
   `/purchase/orders`, and `/menus` returns the SPA rather than a 404.
4. Confirm browser requests reach the API without CORS errors.
5. Register a disposable test account and exercise login, menu, inventory,
   purchase, and order flows.
6. Uploads are not considered persistent until R2 or another durable object
   store is configured and verified.

## Free-tier caveats

Free hosting is for testing, not production. Render Free web services spin down
after 15 minutes of inactivity, have ephemeral local storage, and can be
restarted. Render Free Postgres expires after 30 days, so this plan intentionally
uses a separate Neon database. Neon Free compute scales to zero and has monthly
usage quotas. Cloudflare Pages Free currently allows up to 500 builds per month;
review current provider limits before increasing CI/deployment frequency.

No production deployment, production database migration, domain change, or
production secret modification is part of this staging setup.
