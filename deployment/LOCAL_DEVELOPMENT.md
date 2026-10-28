# Local Docker development

This workflow is separate from the deployment/release Compose files. Use only
`deployment/docker-compose.dev.yml`; do not use the deployment, release,
rollback, or protected local overlay files for this workflow.

## Services and URLs

- Frontend: <http://127.0.0.1:5173>
- Backend API: <http://127.0.0.1:8000/api/>
- PostgreSQL: internal Compose service `db:5432`; no host port is published.
- Redis: internal Compose service `redis:6379`; no host port is published.

The browser API URL deliberately uses `127.0.0.1:8000`; the Docker-only
hostname `backend` would not resolve in the user's browser. Vite's Docker
configuration enables polling so file changes under Windows bind mounts are
observed. The frontend source mount is read-only; its dependencies live in a
separate project-scoped named volume. Backend code directories are mounted
read-only, and Django's development server reloads on code changes. Backend
dependencies remain in the image's Python installation and are not hidden by
the source mounts.

The backend receives `USE_SQLITE=False`, `DB_HOST=db`, and the same database
name/user/password values as the PostgreSQL service. `PYTHON_DOTENV_DISABLED=1`
prevents the mounted source tree or any image path from causing python-dotenv
to load a backend `.env` file. The stack does not mount the repository's
SQLite database or backend environment file. No migration or seed command runs
automatically.

## Private credentials

Create a private, operator-managed environment file outside the repository,
for example `%LOCALAPPDATA%\EatHub\docker-dev.env`, with these variable names:

```text
DEV_DB_NAME
DEV_DB_USER
DEV_DB_PASSWORD
DEV_DJANGO_SECRET_KEY
```

Supply local-only values using a trusted password manager or secure editor.
Restrict the directory and file ACLs to the Windows account that operates this
development stack. For a new directory, the operator can establish a
user-only directory ACL from PowerShell before creating the file:

```powershell
$SecretDir = Join-Path $env:LOCALAPPDATA 'EatHub'
if (Test-Path -LiteralPath $SecretDir) { throw 'Review the existing directory and ACL before reuse.' }
New-Item -ItemType Directory -Path $SecretDir | Out-Null
icacls $SecretDir /inheritance:r
icacls $SecretDir /grant:r "$($env:USERDOMAIN)\$($env:USERNAME):(OI)(CI)F"
```

Create `docker-dev.env` in that directory through the secure editor, and
confirm its ACL inherits only that account's access. Do not place real values in this repository, a Dockerfile,
PowerShell command text, or shell history. Do not print the file or the output
of `docker compose config`; resolved Compose configuration includes secrets.
Compose receives only the file path on the command line. Values are passed to
the local containers as runtime environment variables and are not baked into
image layers. Anyone with access to the Docker daemon can inspect container
environment, so use only disposable local credentials and a Docker Desktop
account trusted with them.

Compose gives inherited process environment variables precedence over values
in `--env-file`. Before startup, stop if any of the four `DEV_*` names are
already set in the PowerShell process; do not let an unnoticed override select
another database or secret.

## First-start isolation gate

The project name is fixed as `eathub-manual-dev`; Compose scopes its containers,
network, and named volumes to this project. The first startup must create a new
PostgreSQL volume. Do not start if this project already has containers or any
of its volumes: inspect the resource labels and resolve ownership separately.
Never attach the deployment database volume or another project's volume.

Run these read-only checks from the repository root in PowerShell before the
first `up`:

```powershell
$Project = 'eathub-manual-dev'
$EnvFile = Join-Path $env:LOCALAPPDATA 'EatHub\docker-dev.env'
$Compose = @('compose', '--project-name', $Project, '--env-file', $EnvFile, '-f', 'deployment/docker-compose.dev.yml')

if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) { throw 'Private development env file is missing.' }
$DevOverrides = @('DEV_DB_NAME', 'DEV_DB_USER', 'DEV_DB_PASSWORD', 'DEV_DJANGO_SECRET_KEY') | Where-Object { Test-Path "Env:\$_" }
if ($DevOverrides.Count -gt 0) { throw ("Clear inherited process variables before continuing: " + ($DevOverrides -join ', ')) }

$null = docker version --format '{{.Server.Version}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker Engine is unavailable.' }
$ExistingProjectContainers = @(docker ps -a --filter "label=com.docker.compose.project=$Project" --format '{{.ID}} {{.Names}} {{.Status}}')
if ($LASTEXITCODE -ne 0) { throw 'Could not verify existing project containers.' }
$ExistingProjectVolumes = @(docker volume ls --filter "label=com.docker.compose.project=$Project" --format '{{.Name}}')
if ($LASTEXITCODE -ne 0) { throw 'Could not verify existing project volumes.' }
$ExpectedVolumes = @("${Project}_dev_postgres_data", "${Project}_dev_media", "${Project}_frontend_node_modules")
$AllVolumeNames = @(docker volume ls --format '{{.Name}}')
if ($LASTEXITCODE -ne 0) { throw 'Could not verify existing volume names.' }
$ExistingExpectedVolumes = @($ExpectedVolumes | Where-Object { $AllVolumeNames -contains $_ })
$ExistingProjectNetworks = @(docker network ls --filter "label=com.docker.compose.project=$Project" --format '{{.Name}}')
if ($LASTEXITCODE -ne 0) { throw 'Could not verify existing project networks.' }
if ($ExistingProjectContainers.Count -gt 0 -or $ExistingProjectVolumes.Count -gt 0 -or $ExistingExpectedVolumes.Count -gt 0 -or $ExistingProjectNetworks.Count -gt 0) { throw 'Project resources already exist; do not reuse them for first initialization.' }

foreach ($Port in @(5173, 8000)) {
    if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) { throw "Required loopback port $Port is already occupied." }
}

docker @Compose config --services
if ($LASTEXITCODE -ne 0) { throw 'Compose preflight failed; do not start services.' }
```

The final command validates interpolation and lists service names only; it
does not print resolved credentials. If the first-start check finds any
existing project resources, stop. Do not delete them or choose a different
project name without reviewing ownership first. On later restarts, preserve and
reuse only the volume created by this workflow.

## Build and start

After the first-start gate passes and the service list is exactly `db`,
`redis`, `backend`, and `frontend`, start only this development project:

```powershell
docker @Compose up --build -d db redis backend frontend
if ($LASTEXITCODE -ne 0) { throw 'Development stack did not start successfully.' }
```

The database health check must pass before the backend starts. The backend
health check verifies its HTTP server socket is listening; the frontend check
verifies that Vite serves the application. Check status and inspect logs
locally, taking care not to share any output containing credentials:

```powershell
docker @Compose ps
docker @Compose logs --tail 100 db redis backend frontend
```

Open <http://127.0.0.1:5173> for manual UI testing. API requests from the
browser go to <http://127.0.0.1:8000/api/>. The database and Redis ports are
not published to Windows. These checks establish process/service readiness,
not application correctness or successful authentication.

## Verify the database target before migration

Before any migration, verify the backend's effective settings without opening
a Django database connection. From the repository root, while the backend is
running:

```powershell
$SettingsProbe = @'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EatHub.settings")
from django.conf import settings
from django.db import connections
aliases = list(settings.DATABASES)
assert aliases == ["default"], aliases
db = settings.DATABASES["default"]
connection = connections["default"]
print({"aliases": aliases, "engine": db["ENGINE"], "name": db["NAME"], "host": db.get("HOST"), "port": db.get("PORT"), "user": db.get("USER"), "sqlite_enabled": os.environ.get("USE_SQLITE"), "connection_open": connection.connection is not None})
'@
docker @Compose exec -T backend python -c $SettingsProbe
if ($LASTEXITCODE -ne 0) { throw 'Settings-only database preflight failed.' }
```

Proceed only if the output shows one PostgreSQL default database, host `db`,
port `5432`, the exact local development database/user from the private
configuration, SQLite disabled, and `connection_open` false. Then independently
confirm the running `db` service belongs to this Compose project and its mount
is the newly created `eathub-manual-dev` volume. A settings-only check proves
where Django is configured to connect; it does not authenticate or prove the
database catalog. If actual database identity/readiness is ambiguous, stop and
have the operator authorize a read-only identity query against this new
development service before migration.

Only after those checks, and as a separate explicit operator action, apply
migrations to the verified development database:

```powershell
docker @Compose exec backend python manage.py migrate
```

Do not run this command against an unverified or existing database. Do not
import data from another database. This workflow does not seed business data.

## Logs and shutdown

```powershell
docker @Compose logs --follow backend frontend
docker @Compose stop
```

`stop` preserves all containers and volumes. To resume, repeat the commands
using the same project and private env file, and verify the existing project
resources belong to this development workflow before starting them.

**Warning:** the `eathub-manual-dev_dev_postgres_data` volume contains the
development database. Removing it destroys that data. Do not use `down -v`,
`docker volume rm`, or prune commands as routine shutdown or troubleshooting.
This workflow does not provide automatic cleanup.

## Reproducibility limits

The Compose topology and service configuration are fixed, and the frontend
dependencies are installed with the repository lockfile. The backend
`requirements.txt` uses minimum-version ranges rather than a complete lock, and
the base images use major/minor tags. Therefore rebuilds are operationally
consistent but not guaranteed byte-for-byte reproducible. Pinning backend
dependencies and image digests is a separate maintenance decision.
