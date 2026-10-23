# Production release and rollback

Production is a single active Docker Compose stack per host. The fixed
`container_name` values and published ports prevent side-by-side stacks on the
same host. The workflow builds versioned images on that host; this repository
does not configure a registry, image backup, or volume backup.

## Identities and operator inputs

- `DEPLOYMENT_NAMESPACE` is the stable lowercase slug for this host/stack:
  `[a-z0-9]+(-[a-z0-9]+)*`, at most 40 characters.
- `STATIC_ASSET_ATTEMPT` identifies one build/collection/deployment attempt. It
  must match
  `YYYYMMDDtHHMMSSz-<12 lowercase hex revision characters>-<8 lowercase hex nonce>`.
  The timestamp is UTC. Generate it from the source commit and a new random
  nonce; for example:

  ```sh
  attempt="$(date -u +%Y%m%dt%H%M%Sz)-$(git rev-parse --short=12 HEAD)-$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')"
  ```

  The wrapper validates the format and calendar date, records the attempt
  before building, and refuses a previously recorded ID or an existing image
  tag/static volume. Never reuse an ID after success, failure, or interruption.
  A failed collector may have written partial files; a fresh ID selects a new
  image tag and empty volume on retry.
- `EATHUB_READINESS_URL` is the HTTPS origin served by the local Nginx virtual
  host, with no path or query. The wrapper pins the request to `127.0.0.1` using
  that hostname, so it checks this host's Nginx route and still validates TLS.
  The tracked Nginx host is `eathub.ir`; operators must confirm that this is the
  intended production virtual host before invoking the wrapper.
- `EATHUB_RELEASE_STATE_DIR` is an absolute, private directory (mode 700 or
  stricter) outside the checkout. Prepare it for the deploy account and retain
  it across deployments. It stores attempt records, successful release records,
  private command logs, a lock, and the active-release pointer. Do not delete
  records or manually remove a stale lock without first checking host state.
- `VITE_API_BASE_URL` and `VITE_BASE_URL` are public browser build values. Supply
  them in the process environment; never put credentials in them. The wrapper
  does not print their values.
- `DB_NAME`, `DB_USER`, and `DB_PASSWORD` must be supplied to Compose through
  the wrapper process environment. The wrapper checks only that they are
  non-empty and never prints their values. The repository does not establish a
  safe interpolation source for them; inject them through the approved operator
  mechanism without reading or copying protected environment files.

The backend exposes unauthenticated `GET /api/ready/`. Compose derives
`EATHUB_RELEASE_ID=success-<attempt-id>` from the explicit
`STATIC_ASSET_ATTEMPT` input for the backend, Celery, collector, and frontend
build. This is the same attempt used in the image tags and static-volume name;
the wrapper computes the expected successful ID from its validated attempt
argument and does not read it back from a mutable image tag.
The endpoint returns only `ready:<release-id>` when the value has the expected
format and a valid UTC timestamp; missing or malformed values return HTTP 503
with a constant `not_ready` body. Responses are marked `Cache-Control: no-store`.
It does not report database, Redis, Celery, or general application dependency
health. The frontend image receives the same release ID as an image label; the
wrapper checks the label and the exact image ID used by the running container.

After activation, the wrapper polls the local Nginx HTTPS route for up to 60
seconds and requires the response body to equal the exact expected release ID.
A generic
HTTP 2xx or a response from an older backend cannot satisfy this check. The
same check is used after rollback. Release and rollback remain unverified until
the non-production runtime path has been exercised.

Compose's required-variable interpolation rejects unset or empty values; it
does not prove historical uniqueness. The wrapper checks the persistent local
state directory and Docker's local image/volume names. If that state is lost,
the record of previously used attempt IDs is lost too.

## Release procedure

After the contract and deployment path have been validated in a non-production
environment, run on the production host from a reviewed, committed checkout.
The wrapper
refuses dirty or untracked backend, frontend, and release-configuration paths.
It also refuses untracked files in the backend or frontend build contexts. Set
the operator-approved values without placing secrets in command history, then
invoke a fresh attempt:

```sh
export DEPLOYMENT_NAMESPACE='production'
export EATHUB_RELEASE_STATE_DIR='/var/lib/eathub/release-state'
export EATHUB_READINESS_URL='https://eathub.ir'
export VITE_API_BASE_URL='<operator-supplied-public-api-url>'
export VITE_BASE_URL='<operator-supplied-public-base-url>'
# Supply DB_NAME, DB_USER, and DB_PASSWORD through the approved secure
# process-environment mechanism; do not put secret values in shell history.
attempt="$(date -u +%Y%m%dt%H%M%Sz)-$(git rev-parse --short=12 HEAD)-$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')"
bash deployment/release.sh release "$attempt"
```

Replace placeholders before execution. Prepare the state directory with mode
700. The wrapper requires non-empty database interpolation variables in its
process environment but never prints them. Do not put secrets in command
history.

The wrapper records a started attempt and the full Git source revision, checks
that its image tags and static volume have never been used, and builds backend
and frontend images with attempt-specific tags. Backend, Celery, and the
collector use exactly the same backend image reference. It then runs only the
collector in the release Compose configuration and waits for its exit status.
The release configuration also declares Nginx's successful-completion
dependency. If collection fails, the wrapper stops before starting the runtime
stack and records a failed attempt.

Only after collection succeeds does the wrapper start the collector-free base
runtime configuration with building and pulling disabled. It compares the
collector container's immutable image ID with the captured backend ID and
verifies that it mounted the expected volume read-write. After activation it
checks backend/frontend/Celery container image IDs and verifies that Nginx
mounted the expected static volume read-only. These checks detect a
wrong artifact after Compose has acted; Compose still consumes tags and the
wrapper cannot prevent a separate Docker operation from racing those tags. Do
not run competing Docker operations during a deployment. A release is not
recorded as successful until release-specific application readiness is
implemented and passes. Successful records are named
`success-<attempt-id>.record` and contain:

- successful release ID, source revision, and attempt ID;
- backend and frontend tags and immutable local Docker image IDs;
- exact static volume name;
- static manifest algorithm, file count, total bytes, and manifest SHA-256;
- deployment timestamp and verification status.

Failed attempts have an attempt record but no successful release record. Their
images, volumes, and logs are retained. A process interruption can leave a
started record or lock; treat the attempt ID as consumed and have an operator
inspect state before resolving a stale lock. The wrapper never clears artifacts
or stale locks automatically.

## Rollback procedure

Choose a `success-<attempt-id>` record with `verification_status=passed` and run:

```sh
bash deployment/release.sh rollback 'success-<recorded-attempt-id>'
```

The wrapper validates the complete release-record schema, checks the namespace,
verifies the backend/frontend image IDs still match their recorded tags, and
verifies the matching static volume exists and that its contents match the
manifest stored in that release's successful record. It performs this content
check before activation and again after activation. After activation it also
checks the backend/frontend/Celery container image IDs and verifies Nginx
mounted that volume read-only. It then uses the rollback Compose configuration. That resolved model
contains no collector service or collector dependency and is configured to use
local images only. Rollback does not build, collect, pull images, or delete
artifacts. It passes the recorded release identity into the backend and requires
the local Nginx readiness response to match that exact identity.

The `current-successful-release` file is an advisory pointer; the immutable
successful release records are authoritative. Rollback always requires an
explicit release ID and never chooses an arbitrary record. If the pointer is
missing or stale, an operator must inspect records and the running container
identities, select the intended verified record explicitly, and then run the
rollback command. The wrapper does not infer or repair the pointer from an
arbitrary previous release. Individual record and pointer replacements are
atomic where the filesystem supports same-directory rename, but updates across
multiple files are not transactional. If a process or disk failure interrupts
those updates, compare the successful record, attempt/rollback record, pointer,
and running container identities before continuing.

Do not rebuild a historical tag from a newer checkout. Tags can be overwritten;
a new build is not proof of the prior image. If any recorded image or volume is
missing or has a different identity, rollback stops. No registry or artifact
backup is configured, so losing the host's Docker images, volumes, or release
state can make exact rollback impossible. Do not improvise by rebuilding or
recollecting into the historical volume.

## Limits and compatibility

The wrapper runs Compose operations sequentially; this is not an atomic cutover,
zero-downtime guarantee, or automatic rollback. Deployment may partially change
services before a readiness failure. The attempt is then failed and retained;
an operator may explicitly roll back to a recorded successful release.

The host needs Bash, GNU coreutils (`stat`, `date`, `od`), Git, and Docker Compose.
The Compose implementation must support `depends_on.condition:
service_completed_successfully`, `pull_policy: never`, and the `up` options
`--no-build` and `--pull`. The wrapper checks the CLI options and asks Compose to
parse both topologies, but runtime behavior—including reuse of a successfully
exited collector container and post-activation image inspection—must be
validated in a non-production environment. The wrapper's post-activation checks
detect image-tag races but cannot eliminate them; serialize all Docker activity
on the host while deploying. Because runtime activation uses `--pull never`,
the host must already have the configured PostgreSQL, Redis, and Nginx images;
the wrapper will fail rather than retrieve missing runtime images.
This workflow assumes one active stack per Docker host because container names
and host ports are fixed. It does not support multiple hosts or artifact
replication.

## Static-content integrity manifest

After the collector exits successfully and before runtime activation, the
wrapper runs the newly built backend image by its captured local image ID. It
mounts only the attempt's static volume at `/app/staticfiles`, read-only, and
runs the standard-library helper `backend/EatHub/static_integrity.py` with
network access disabled. An empty tree, symbolic link, non-regular file,
invalid relative path, unreadable file, or file changing while hashed causes
verification to fail. The wrapper verifies the same manifest again after
activation. Rollback uses the recorded backend image and volume, checks their
manifest before activation, and checks again afterward. No volume is modified
by these verification runs.

Manifest algorithm `eathub-static-manifest-v1` hashes every regular file's
bytes with SHA-256 and records its POSIX relative path, byte size, and file
hash. Entries are sorted by UTF-8 path bytes and serialized as canonical JSON
(ASCII escaping, sorted object keys, no insignificant whitespace); the
`static_manifest_sha256` field is SHA-256 of that canonical JSON. The record
also stores the algorithm, positive file count, and total bytes. Rollback
rejects a missing or malformed manifest or any mismatch, so successful
records made before this schema was introduced are not eligible for rollback
through the updated wrapper.

This is a deterministic comparison between the retained volume and metadata
captured after collection. It detects an empty or changed tree and makes
accidental truncation or replacement visible. It does not prove that Django
collected every semantically required asset, that files are correct for the
application, or that Nginx successfully serves every path. It is not an
independent authenticity proof: the release record and Docker volume are both
stored on the same host, and an administrator able to alter both can replace
both. The scan is not an atomic filesystem snapshot; serialize Docker and
volume operations, and do not mutate release volumes while verification or
deployment is in progress. Frontend image identity is checked separately and
is not part of the static-volume manifest.

The static volume is separate from the uploaded-media bind mount and database
volume. Old images and static volumes are retained during normal release and
rollback; cleanup or backups require a separate reviewed operational procedure.
