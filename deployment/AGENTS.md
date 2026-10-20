# Eathub Deployment Guidelines

This directory contains the deployment and infrastructure configuration
for the Eathub platform.

The deployment layer is responsible for running and exposing the
application in development, staging, and production environments.

The deployment layer must NOT contain business logic.

---

# 1. Project Context

Eathub is a multi-tenant ERP platform.

The repository contains:

- Django backend
- React + TypeScript frontend
- PostgreSQL database
- Nginx reverse proxy
- Docker-based deployment
- Static and media file handling
- HTTPS / TLS configuration

The deployment layer must support the application without coupling
infrastructure configuration to domain/business rules.

---

# 2. Deployment Responsibilities

The deployment directory is responsible for:

- Docker configuration
- Docker Compose configuration
- Nginx configuration
- Reverse proxy configuration
- HTTPS / TLS configuration
- Static file serving
- Media file serving
- Network configuration
- Container configuration
- Environment-specific configuration
- Production runtime configuration
- Health checks
- Service dependencies

The deployment layer must NOT implement:

- Business logic
- ERP workflows
- Inventory logic
- Purchase logic
- Sales logic
- Authentication business rules
- RBAC business rules
- Domain entities
- Application use cases

Those responsibilities belong to the application code.

---

# 3. Repository Structure

Follow the existing repository structure.

A typical structure may look like:

    deployment/
    ├── docker/
    │   ├── backend/
    │   ├── frontend/
    │   └── nginx/
    │
    ├── nginx/
    │   ├── nginx.conf
    │   └── conf.d/
    │
    ├── scripts/
    │
    ├── production/
    │
    ├── staging/
    │
    └── development/

Do NOT create directories only because they are mentioned in this
document.

Always inspect the existing repository before introducing new
deployment structure.

Prefer the existing project conventions.

---

# 4. General Rules

Before modifying deployment files:

1. Inspect the existing deployment configuration.
2. Understand how services communicate.
3. Check Docker Compose dependencies.
4. Check environment variables.
5. Check exposed ports.
6. Check volumes.
7. Check Nginx routing.
8. Check SSL configuration.
9. Check static/media configuration.
10. Check backend and frontend build/runtime requirements.

Do not make assumptions about the infrastructure.

Do not rewrite the deployment architecture unless explicitly requested.

Do not modify unrelated application code while working on deployment.

---

# 5. Docker Rules

Use Docker consistently with the existing project.

Before modifying Docker configuration:

- Inspect existing Dockerfiles.
- Inspect docker-compose files.
- Inspect service names.
- Inspect networks.
- Inspect volumes.
- Inspect health checks.
- Inspect environment variables.
- Inspect exposed ports.

Prefer reproducible builds.

Avoid:

- `latest` tags for production-critical infrastructure
- unnecessary privileged containers
- unnecessary host networking
- unnecessary exposed ports
- running services as root when avoidable
- embedding secrets in Dockerfiles
- embedding secrets in docker-compose files

---

# 6. Docker Images

Production images should be:

- Minimal
- Reproducible
- Version-pinned where appropriate
- Free from development-only dependencies

Do not copy unnecessary files into production images.

Use `.dockerignore`.

Do not include:

- `.git`
- `.venv`
- `node_modules`
- local secrets
- `.env`
- cache directories
- test artifacts

unless there is a specific reason.

---

# 7. Backend Container

The Django backend is a production application.

The production backend container should:

- use a production WSGI/ASGI server
- not use Django development server
- collect static files during deployment
- load configuration from environment variables
- expose only the required internal port
- run database migrations through an explicit deployment process

Do NOT use:

    python manage.py runserver

as the production application server.

Use the existing project convention for:

- Gunicorn
- Uvicorn
- ASGI
- WSGI

Do not replace the server technology unless explicitly requested.

---

# 8. Django Configuration

Deployment configuration must respect Django's separation between:

- development
- staging
- production

Never enable production configuration accidentally in local development.

Production must ensure:

- `DEBUG=False`
- correct `ALLOWED_HOSTS`
- correct CORS configuration
- correct CSRF trusted origins
- secure cookies where HTTPS is enabled
- secure session cookies
- secure CSRF cookies
- correct proxy/HTTPS headers

Never hardcode production secrets.

---

# 9. Database

Eathub uses PostgreSQL.

Deployment configuration must treat PostgreSQL as persistent infrastructure.

Do NOT:

- delete database volumes casually
- recreate production databases unnecessarily
- use SQLite in production
- expose PostgreSQL publicly unless explicitly required
- hardcode database credentials

Database credentials must come from environment variables or a
secure secret-management mechanism.

Before changing database configuration, inspect:

- database service
- database hostname
- database port
- database name
- username
- password configuration
- volumes
- health checks
- migration workflow

---

# 10. Database Migrations

Migrations are part of the application deployment process.

Never silently delete or rewrite existing migrations to solve a
deployment problem.

Do NOT run destructive migration commands automatically.

Never use:

    migrate --fake

or other migration bypasses unless explicitly instructed.

Before modifying migration-related deployment behavior:

1. Inspect current migration state.
2. Inspect migration files.
3. Run Django checks.
4. Run migrations in a controlled environment.

Production migrations must be executed deliberately.

---

# 11. Nginx

Nginx acts as the reverse proxy and public HTTP/HTTPS entry point.

Typical routing may include:

    Client
       |
       v
    Nginx
       |
       +----> Frontend
       |
       +----> Django API
       |
       +----> Static
       |
       +----> Media

Respect the existing routing architecture.

Do not expose internal services directly unless explicitly required.

---

# 12. Nginx API Routing

API routes should be proxied to the backend service.

Example conceptual structure:

    /api/
        |
        v
    Django backend

Do not introduce API routing changes without checking the existing
frontend API client configuration.

If changing an API prefix, verify:

- frontend API base URL
- backend URL configuration
- authentication endpoints
- CORS configuration
- CSRF configuration
- Nginx proxy rules

---

# 13. Frontend

The React frontend should be built for production.

Do NOT run the development server in production.

Do NOT use:

    npm run dev

as the production frontend server.

The production flow should generally be:

    source
      |
      v
    npm install / npm ci
      |
      v
    npm run build
      |
      v
    production static assets
      |
      v
    Nginx

Use the existing package manager and project scripts.

Do not replace npm/pnpm/yarn without inspecting the repository first.

---

# 14. Frontend Environment Variables

Frontend environment variables must be treated carefully.

Remember:

Frontend environment variables are generally visible to the browser
after the application is built.

Therefore:

NEVER put secrets in frontend environment variables.

Do NOT expose:

- database passwords
- Django secret key
- JWT signing secrets
- private API keys
- cloud provider private credentials
- SMTP passwords

Only public configuration may be exposed to the frontend.

---

# 15. Secrets

Secrets must NEVER be committed to Git.

Never write secrets into:

- Dockerfiles
- docker-compose files
- Nginx configs
- shell scripts
- frontend source code
- backend source code
- AGENTS.md
- README files

Examples of secrets include:

- database passwords
- Django `SECRET_KEY`
- JWT signing keys
- API keys
- SMTP credentials
- cloud credentials
- private certificates

Use environment variables or the project's configured secret-management
system.

If a secret is accidentally discovered in the repository, do NOT copy
or expose it in a response.

Report the issue and recommend rotating the secret.

---

# 16. Environment Files

Never commit real production `.env` files.

Use:

    .env.example

for documenting required variables.

The example file must contain placeholders, for example:

    DATABASE_NAME=
    DATABASE_USER=
    DATABASE_PASSWORD=
    SECRET_KEY=
    ALLOWED_HOSTS=

Never place real credentials in `.env.example`.

---

# 17. HTTPS / TLS

Production traffic should use HTTPS.

Nginx should:

- terminate TLS
- redirect HTTP to HTTPS when appropriate
- proxy requests securely
- pass the correct HTTPS/proxy headers

Do not disable TLS verification or security checks just to make a
deployment work.

Do not delete certificates or ACME configuration without explicit
authorization.

When changing TLS configuration, inspect:

- certificate paths
- private key paths
- renewal mechanism
- domain configuration
- HTTP challenge requirements
- DNS configuration

---

# 18. Static Files

Django static files must be handled using the project's configured
static collection process.

Typical flow:

    Django
       |
       v
    collectstatic
       |
       v
    STATIC_ROOT
       |
       v
    Nginx

Do not change:

- `STATIC_ROOT`
- `STATIC_URL`
- volume mounts
- Nginx static aliases

without checking all dependent configuration.

---

# 19. Media Files

Media files are user/application-generated files.

Examples:

- uploaded images
- menu images
- documents
- receipts
- invoices
- attachments

Media must not accidentally be mixed with static files.

Respect the existing:

    MEDIA_ROOT
    MEDIA_URL

configuration.

Do not delete media volumes during normal deployments.

---

# 20. Volumes

Persistent data must use persistent volumes.

Typical persistent resources include:

- PostgreSQL data
- media files
- uploaded documents
- certificates, if managed locally

Never run destructive volume commands on production without explicit
authorization.

Especially avoid:

    docker compose down -v

in production.

That command may destroy persistent application data.

---

# 21. Networking

Prefer private Docker networks for internal services.

Typical architecture:

    Internet
       |
       v
    Nginx
       |
       +--------> Frontend
       |
       +--------> Backend
                    |
                    v
                 PostgreSQL

PostgreSQL should normally be accessible only from the application
network.

Do not expose internal service ports to the public internet unless
explicitly required.

---

# 22. Service Health

Where appropriate, use health checks for:

- PostgreSQL
- Django backend
- Nginx
- other critical services

Service startup ordering should not rely solely on:

    depends_on

when application readiness is required.

Prefer health-aware dependency handling where supported.

---

# 23. Restart Policies

Production services should have appropriate restart policies.

However, restart policies must not hide application failures.

If a service repeatedly crashes:

1. Inspect logs.
2. Identify the root cause.
3. Fix the underlying issue.

Do not simply increase restart behavior to hide failures.

---

# 24. Logging

Deployment configuration should allow useful logs for:

- Nginx
- Django
- Gunicorn/Uvicorn
- PostgreSQL
- Docker services

Do not log:

- passwords
- API keys
- JWT secrets
- session secrets
- sensitive user data

Prefer structured or clearly identifiable logs where supported.

---

# 25. Resource Configuration

Do not introduce arbitrary CPU or memory limits without understanding
the workload.

If resource limits are changed:

- document the reason
- consider production workload
- consider PostgreSQL requirements
- consider backend worker count
- consider frontend build requirements

---

# 26. Production Safety

Production is the highest-risk environment.

Before making production deployment changes:

1. Inspect current configuration.
2. Review the proposed change.
3. Check for destructive operations.
4. Check data persistence.
5. Check rollback options.
6. Validate configuration syntax.
7. Run relevant tests/checks.
8. Prefer incremental changes.

Never perform destructive operations automatically.

---

# 27. Forbidden Operations Without Explicit Approval

Never perform these operations against production without explicit
authorization:

- deleting database volumes
- deleting media volumes
- dropping databases
- resetting migrations
- deleting TLS certificates
- deleting production containers when data loss is possible
- changing production secrets
- rotating credentials
- modifying DNS records
- changing firewall rules
- opening internal ports publicly

---

# 28. Validation Before Deployment

Before deploying changes, perform appropriate validation.

For Docker:

    docker compose config

For Django:

    python manage.py check

For migrations:

    python manage.py makemigrations --check
    python manage.py migrate --plan

For frontend:

    npm run build

Use the actual package manager and commands defined by the repository.

Do not invent commands if the project already defines equivalent
scripts.

---

# 29. Deployment Changes Must Be Minimal

When fixing a deployment problem:

Prefer:

    smallest safe change

over:

    rewrite the entire deployment configuration

Do not refactor unrelated infrastructure while solving a specific
deployment issue.

Keep changes focused and reviewable.

---

# 30. Development Environment

Local development may use:

- Django development server
- React development server
- local PostgreSQL
- Docker services

Development configuration must remain convenient for developers.

Do not impose production-only restrictions on local development unless
required.

---

# 31. Staging Environment

If staging exists, it should resemble production as closely as
practical.

Staging should be used to validate:

- Docker builds
- migrations
- Nginx configuration
- frontend builds
- backend startup
- API routing
- static files
- media files
- HTTPS behavior where applicable

Do not assume that successful local development guarantees production
success.

---

# 32. CI/CD

If CI/CD exists:

- inspect existing pipelines before modifying them
- preserve existing secrets handling
- avoid duplicating deployment logic
- keep builds reproducible
- run automated tests before deployment where appropriate

Do not create a new CI/CD platform without explicit authorization.

---

# 33. Git

Deployment configuration is version-controlled.

Before modifying infrastructure:

    git status

After modifications:

    git diff

Review all deployment changes before committing.

Do not commit:

- `.env`
- secrets
- certificates/private keys
- generated files
- local Docker state

---

# 34. Codex Behavior

When working in this directory, Codex must:

1. Inspect existing configuration before editing.
2. Understand service dependencies.
3. Avoid destructive operations.
4. Avoid exposing secrets.
5. Avoid unrelated refactoring.
6. Prefer minimal changes.
7. Validate configuration after changes.
8. Report modified files.
9. Report commands executed.
10. Report any unresolved deployment risks.

Do not assume that a configuration is unused merely because it is not
referenced immediately.

Search the repository before removing or renaming deployment files.

---

# 35. When Unsure

If a deployment change could:

- cause data loss
- expose a service
- change authentication
- break HTTPS
- change DNS
- change database behavior
- delete persistent data
- rotate secrets
- affect production availability

STOP and ask for explicit confirmation.

Do not guess.

---

# 36. Final Principle

Deployment should be:

- Reproducible
- Secure
- Observable
- Minimal
- Reversible
- Environment-aware

The goal is not to make deployment configuration complicated.

The goal is to make Eathub deploy reliably without introducing
security issues, data loss, or environment-specific surprises.