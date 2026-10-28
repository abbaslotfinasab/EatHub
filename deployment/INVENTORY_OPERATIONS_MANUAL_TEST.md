# Inventory operations manual test runbook

Use this only with the dedicated `eathub-manual-dev` Compose project. Do not
use the deployment, release, rollback, or protected local Compose files. This
runbook does not authorize migration or stock-changing actions by itself.

## 1. Read-only environment and database checks

Run from the repository root in PowerShell. These checks do not mutate the
database:

```powershell
$Project = 'eathub-manual-dev'
$EnvFile = Join-Path $env:LOCALAPPDATA 'EatHub\docker-dev.env'
$Compose = @('compose', '--project-name', $Project, '--env-file', $EnvFile, '-f', 'deployment/docker-compose.dev.yml')

if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) { throw 'Private development env file is missing.' }
docker @Compose ps
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the dedicated Compose project.' }
$DbId = (docker @Compose ps -q db).Trim()
if ($LASTEXITCODE -ne 0 -or -not $DbId) { throw 'The expected db service is not present.' }
docker inspect --format '{{.Id}} {{.Name}} {{.State.Status}} {{.State.Health.Status}} {{index .Config.Labels "com.docker.compose.project"}} {{range .Mounts}}{{.Name}}=>{{.Destination}} {{end}}' $DbId
if ($LASTEXITCODE -ne 0) { throw 'Could not verify the database container identity and volume.' }
```

Stop unless the project label is `eathub-manual-dev`, the service is healthy,
and its data mount is the project-scoped `eathub-manual-dev_dev_postgres_data`
volume created by this workflow. Do not attach or reuse another project's
volume. Do not print `docker compose config` output because it includes
resolved secrets.

Inspect Django's configured target without opening a database connection, then
query the dedicated database for its own identity:

```powershell
$SettingsProbe = @'
from django.conf import settings
from django.db import connections
assert list(settings.DATABASES) == ['default']
db = settings.DATABASES['default']
connection = connections['default']
print({'engine': db['ENGINE'], 'name': db['NAME'], 'host': db['HOST'], 'port': db['PORT'], 'user': db['USER'], 'sqlite_enabled': __import__('os').environ.get('USE_SQLITE'), 'connection_open': connection.connection is not None})
'@
docker @Compose exec -T backend python -c $SettingsProbe
if ($LASTEXITCODE -ne 0) { throw 'Django settings preflight failed.' }

docker @Compose exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT current_database(), inet_server_addr(), inet_server_port(), current_user;"'
if ($LASTEXITCODE -ne 0) { throw 'Could not query the dedicated database identity.' }
```

Proceed only when Django is configured for PostgreSQL host `db`, port `5432`,
and the same database and role identified by the Compose database service;
SQLite is disabled and `connection_open` is false in the settings probe. The
read-only SQL identity query must confirm the same dedicated service. If any
identity or volume is unexpected, stop without migrating.

Review pending migrations before any write:

```powershell
docker @Compose exec -T backend python manage.py migrate --plan
docker @Compose exec -T backend python manage.py showmigrations accounts inventory
```

These commands inspect migration state; they do not apply migrations. Stop if
the plan includes unexpected operations, the target identity is uncertain, or
the `0006_master_data_invariants` guard reports conflicting master data.

## 2. Explicit migration action

Only after the checks above and operator approval, apply Inventory through the
normal migration graph. This is a database-changing command and may also apply
its unapplied dependencies, including the Accounts permission and Inventory
master-data migrations:

```powershell
docker @Compose exec backend python manage.py migrate inventory 0007_inventory_operations
```

Then verify (read-only):

```powershell
docker @Compose exec -T backend python manage.py showmigrations accounts inventory
docker @Compose exec -T backend python manage.py migrate --check
docker @Compose ps
```

Do not use `--fake`, reset the database, or resolve migration conflicts by
deleting records. Stop and investigate any migration error before retrying.

## 3. Manual workflow checks

Open <http://127.0.0.1:5173> and select a test business with an active user
granted `inventory.view` and `inventory.adjust`. Use items and warehouses
belonging to that business only. The API is at <http://127.0.0.1:8000/api/>.

These actions write business data; perform them only after verifying the
development target and migration state:

1. **Issue:** create a multi-line draft with a reason and reference. Post it,
   replay the same post action, and verify stock was deducted once and one
   `issue` movement per line appears. Try a quantity above available stock and
   confirm the request fails without changing any line's balance.
2. **Transfer:** create a draft between two distinct same-business
   warehouses. Dispatch and verify source stock decreases and the document
   shows the quantity in transit. Receive and verify destination stock
   increases once. Replay dispatch/receipt and verify no duplicate movements.
3. **Stocktake:** create a count snapshot, save physical counts, and approve.
   Verify the variance movement and audit actor appear in history. Separately,
   create another count, post a stock-changing operation after its snapshot,
   then verify approval is rejected as stale; do not retry approval on that
   stale document.
4. **History:** filter movements by type, warehouse, item, reference, date,
   and actor through the API. Confirm the displayed `balance_after` is the
   movement's historical balance, not a current-balance substitute.
5. **Authorization and tenant scope:** repeat a read as a user without
   `inventory.view`, a mutation as a user without `inventory.adjust`, and a
   detail request for another business's document. Expect denial or a scoped
   not-found response without exposing the foreign record.

The current transfer workflow receives the full dispatched quantity at once;
partial receipt and post-dispatch cancellation are not supported. A stale
stocktake must be cancelled and recreated after stock movement rather than
approved or edited to replace its snapshot.

## 4. Readiness and recovery

Check backend/frontend readiness and inspect logs without sharing output that
could contain credentials:

```powershell
docker @Compose ps
Test-NetConnection 127.0.0.1 -Port 8000
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5173/ -TimeoutSec 5
docker @Compose logs --tail 100 backend frontend
```

No migration, seed, or stock operation is automatic. Keep the development
volume for future runs. Removing `eathub-manual-dev_dev_postgres_data` destroys
the development database; do not use `down -v`, volume removal, or prune
commands as routine cleanup.
