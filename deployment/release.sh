#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd -P)"
BASE_FILE="$SCRIPT_DIR/docker-compose.yml"
RELEASE_FILE="$SCRIPT_DIR/docker-compose.release.yml"
ROLLBACK_FILE="$SCRIPT_DIR/docker-compose.rollback.yml"
cd -- "$REPO_ROOT"

valid_namespace() {
    [[ ${#1} -le 40 && $1 =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]
}

valid_attempt_id() {
    [[ $1 =~ ^[0-9]{8}t[0-9]{6}z-[0-9a-f]{12}-[0-9a-f]{8}$ ]] || return 1
    local normalized
    normalized="$(date -u -d "${1:0:8} ${1:9:6}" +%Y%m%dT%H%M%SZ 2>/dev/null)" || return 1
    [[ $normalized == "${1:0:8}T${1:9:6}Z" ]]
}

valid_release_id() {
    [[ $1 =~ ^success-[0-9]{8}t[0-9]{6}z-[0-9a-f]{12}-[0-9a-f]{8}$ ]]
}

attempt_matches_source_revision() {
    valid_attempt_id "$1" || return 1
    [[ $2 =~ ^[0-9a-f]{40}$ ]] || return 1
    [[ ${1:17:12} == "${2:0:12}" ]]
}

valid_timestamp() {
    [[ $1 =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] || return 1
    [[ "$(date -u -d "$1" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)" == "$1" ]]
}

attempt_record_path() { printf '%s/attempt-%s.record' "$STATE_DIR" "$1"; }
release_record_path() { printf '%s/%s.record' "$STATE_DIR" "$1"; }

attempt_is_unused() {
    local id=$1
    valid_attempt_id "$id" || return 1
    [[ ! -e $(attempt_record_path "$id") && ! -e $(release_record_path "success-$id") ]]
}

record_value() {
    local file=$1 key=$2
    awk -F= -v key="$key" '$1 == key { sub(/^[^=]*=/, ""); print; found=1; exit } END { if (!found) exit 1 }' "$file"
}

record_has_release_schema() {
    local file=$1 expected_release_id=$2
    [[ -f $file && ! -L $file ]] || return 1
    awk -F= '
        BEGIN {
            count = split("format status release_id namespace source_revision attempt_id backend_image_tag backend_image_id frontend_image_tag frontend_image_id static_volume_name static_manifest_algorithm static_manifest_files static_manifest_bytes static_manifest_sha256 deployment_timestamp_utc verification_status", keys, " ")
            for (i = 1; i <= count; i++) required[keys[i]] = 1
        }
        {
            if (NF != 2 || !($1 in required) || seen[$1]++) invalid = 1
        }
        END {
            if (invalid || NR != count) exit 1
            for (key in required) if (!seen[key]) exit 1
        }
    ' "$file" || return 1

    [[ $(record_value "$file" format) == 1 ]] &&
        [[ $(record_value "$file" status) == successful ]] &&
        [[ $(record_value "$file" release_id) == "$expected_release_id" ]] &&
        [[ $(record_value "$file" verification_status) == passed ]]
}

record_is_successful() {
    local file=$1 expected_release_id=$2 namespace attempt source_revision backend_tag frontend_tag backend_id frontend_id volume timestamp manifest_algorithm manifest_files manifest_bytes manifest_sha256
    record_has_release_schema "$file" "$expected_release_id" || return 1
    valid_release_id "$expected_release_id" || return 1
    namespace="$(record_value "$file" namespace)"
    attempt="$(record_value "$file" attempt_id)"
    source_revision="$(record_value "$file" source_revision)"
    backend_tag="$(record_value "$file" backend_image_tag)"
    frontend_tag="$(record_value "$file" frontend_image_tag)"
    backend_id="$(record_value "$file" backend_image_id)"
    frontend_id="$(record_value "$file" frontend_image_id)"
    volume="$(record_value "$file" static_volume_name)"
    manifest_algorithm="$(record_value "$file" static_manifest_algorithm)"
    manifest_files="$(record_value "$file" static_manifest_files)"
    manifest_bytes="$(record_value "$file" static_manifest_bytes)"
    manifest_sha256="$(record_value "$file" static_manifest_sha256)"
    timestamp="$(record_value "$file" deployment_timestamp_utc)"

    valid_namespace "$namespace" && attempt_matches_source_revision "$attempt" "$source_revision" &&
        [[ $expected_release_id == "success-$attempt" ]] &&
        [[ $backend_tag == "$(backend_tag_for "$namespace" "$attempt")" ]] &&
        [[ $frontend_tag == "$(frontend_tag_for "$namespace" "$attempt")" ]] &&
        [[ $backend_id =~ ^sha256:[0-9a-f]{64}$ && $frontend_id =~ ^sha256:[0-9a-f]{64}$ ]] &&
        [[ $volume == "$(static_volume_for "$namespace" "$attempt")" ]] &&
        [[ $manifest_algorithm == eathub-static-manifest-v1 ]] &&
        [[ $manifest_files =~ ^[1-9][0-9]*$ ]] &&
        [[ $manifest_bytes =~ ^(0|[1-9][0-9]*)$ ]] &&
        [[ $manifest_sha256 =~ ^[0-9a-f]{64}$ ]] &&
        valid_timestamp "$timestamp"
}

atomic_record() {
    local target=$1 line temporary
    shift
    temporary="$(mktemp "$STATE_DIR/.record.XXXXXX")"
    for line in "$@"; do printf '%s\n' "$line" >> "$temporary"; done
    mv -f -- "$temporary" "$target"
}

backend_tag_for() { printf 'eathub-backend-%s:%s' "$1" "$2"; }
frontend_tag_for() { printf 'eathub-frontend-%s:%s' "$1" "$2"; }
static_volume_for() { printf 'eathub-%s-static-%s' "$1" "$2"; }

die() {
    printf 'release workflow failed at %s: %s\n' "${CURRENT_STAGE:-preflight}" "$1" >&2
    exit 1
}

prepare_state_dir() {
    local requested mode numeric_mode
    requested=${EATHUB_RELEASE_STATE_DIR:-}
    [[ -n $requested && $requested == /* ]] || die 'EATHUB_RELEASE_STATE_DIR must be an absolute path outside the repository'
    [[ ! -L $requested ]] || die 'release state directory must not be a symbolic link'
    mkdir -p -m 700 -- "$requested"
    STATE_DIR="$(cd -- "$requested" && pwd -P)"
    case "$STATE_DIR/" in "$REPO_ROOT/"*) die 'release state directory must be outside the repository' ;; esac
    mode="$(stat -c '%a' -- "$STATE_DIR")" || die 'GNU stat is required to verify state-directory permissions'
    numeric_mode=$((8#$mode))
    (( (numeric_mode & 077) == 0 )) || die 'release state directory must be private (mode 700 or stricter)'
    LOCK_DIR="$STATE_DIR/.lock"
    mkdir -- "$LOCK_DIR" 2>/dev/null || die 'another release operation may be running, or a stale lock needs operator review'
}

write_attempt_state() {
    local status=$1 stage=$2 result=${3:-}
    atomic_record "$ATTEMPT_RECORD" \
        'format=1' "status=$status" "namespace=$DEPLOYMENT_NAMESPACE" \
        "attempt_id=$ATTEMPT_ID" "source_revision=${SOURCE_REVISION:-unknown}" \
        "backend_image_tag=$BACKEND_TAG" "backend_image_id=${BACKEND_IMAGE_ID:-}" \
        "frontend_image_tag=$FRONTEND_TAG" "frontend_image_id=${FRONTEND_IMAGE_ID:-}" \
        "static_volume_name=$STATIC_VOLUME" \
        "static_manifest_algorithm=${STATIC_MANIFEST_ALGORITHM:-}" \
        "static_manifest_files=${STATIC_MANIFEST_FILES:-}" \
        "static_manifest_bytes=${STATIC_MANIFEST_BYTES:-}" \
        "static_manifest_sha256=${STATIC_MANIFEST_SHA256:-}" \
        "stage=$stage" "result=$result" \
        "updated_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}

finish_operation() {
    local rc=$?
    trap - EXIT
    if (( rc != 0 )) && [[ -n ${ATTEMPT_RECORD:-} && -f ${ATTEMPT_RECORD:-} && ${ATTEMPT_FINALIZED:-0} == 0 ]]; then
        write_attempt_state failed "$CURRENT_STAGE" "exit-$rc" 2>/dev/null || true
    fi
    if (( rc != 0 )) && [[ -n ${ROLLBACK_RECORD:-} && -f ${ROLLBACK_RECORD:-} && ${ROLLBACK_FINALIZED:-0} == 0 ]]; then
        atomic_record "$ROLLBACK_RECORD" 'format=1' 'status=failed' \
            "release_id=$TARGET_RELEASE_ID" "stage=$CURRENT_STAGE" "result=exit-$rc" \
            "updated_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" 2>/dev/null || true
    fi
    [[ -n ${LOCK_DIR:-} ]] && rmdir -- "$LOCK_DIR" 2>/dev/null || true
    exit "$rc"
}

run_logged() {
    local label=$1 rc
    shift
    CURRENT_STAGE=$label
    LAST_LOG="$STATE_DIR/${OPERATION_ID}-${label}.log"
    if "$@" >"$LAST_LOG" 2>&1; then
        return 0
    else
        rc=$?
        printf 'Command failed during %s (exit %s); output was kept in the private state directory.\n' "$label" "$rc" >&2
        return "$rc"
    fi
}

readiness_host() {
    local url=$1 host
    [[ $url =~ ^https://([A-Za-z0-9.-]+)/?$ ]] || return 1
    host=${BASH_REMATCH[1]}
    [[ $host =~ ^[A-Za-z0-9.-]+$ && $host != .* && $host != *. ]] || return 1
    printf '%s' "$host"
}

check_readiness() {
    local expected_release_id=$1 host body attempt
    valid_release_id "$expected_release_id" || return 1
    host="$(readiness_host "${EATHUB_READINESS_URL:-}")" || return 1
    for ((attempt = 0; attempt < 20; attempt++)); do
        if body="$(curl --noproxy '*' --fail --silent --show-error --connect-timeout 1 --max-time 2 \
            --resolve "$host:443:127.0.0.1" "https://$host/api/ready/")" &&
            [[ $body == "ready:$expected_release_id" ]]; then
            return 0
        fi
        (( attempt == 19 )) || sleep 1
    done
    return 1
}

require_release_specific_readiness() {
    local host
    command -v curl >/dev/null || return 1
    host="$(readiness_host "${EATHUB_READINESS_URL:-}")" || return 1
    [[ -n $host ]]
}

require_compose_database_inputs() {
    local name value
    for name in DB_NAME DB_USER DB_PASSWORD; do
        case $name in
            DB_NAME) value=${DB_NAME:-} ;;
            DB_USER) value=${DB_USER:-} ;;
            DB_PASSWORD) value=${DB_PASSWORD:-} ;;
        esac
        [[ -n $value ]] || die "$name must be supplied to Compose through the wrapper process environment"
    done
}

assert_image_tag_id() {
    local tag=$1 expected=$2 actual
    actual="$(docker image inspect --format '{{.Id}}' "$tag")" || return 1
    [[ $actual == "$expected" ]]
}

assert_frontend_release_id() {
    local image=$1 expected=$2 actual
    actual="$(docker image inspect --format '{{ index .Config.Labels "com.eathub.release-id" }}' "$image")" || return 1
    [[ $actual == "$expected" ]]
}

verify_recorded_artifacts() {
    local backend_tag=$1 backend_id=$2 frontend_tag=$3 frontend_id=$4 release_id=$5 volume=$6
    assert_image_tag_id "$backend_tag" "$backend_id" &&
        assert_image_tag_id "$frontend_tag" "$frontend_id" &&
        assert_frontend_release_id "$frontend_tag" "$release_id" &&
        docker volume inspect "$volume" >/dev/null 2>&1
}

parse_static_manifest() {
    local summary=$1
    local -a lines=()
    mapfile -t lines <<< "$summary"
    [[ ${#lines[@]} == 4 ]] || return 1
    [[ ${lines[0]} == 'algorithm=eathub-static-manifest-v1' ]] || return 1
    [[ ${lines[1]} == files=* && ${lines[2]} == bytes=* && ${lines[3]} == sha256=* ]] || return 1
    STATIC_MANIFEST_ALGORITHM=${lines[0]#algorithm=}
    STATIC_MANIFEST_FILES=${lines[1]#files=}
    STATIC_MANIFEST_BYTES=${lines[2]#bytes=}
    STATIC_MANIFEST_SHA256=${lines[3]#sha256=}
    [[ $STATIC_MANIFEST_FILES =~ ^[1-9][0-9]*$ ]] || return 1
    [[ $STATIC_MANIFEST_BYTES =~ ^(0|[1-9][0-9]*)$ ]] || return 1
    [[ $STATIC_MANIFEST_SHA256 =~ ^[0-9a-f]{64}$ ]]
}

calculate_static_manifest() {
    local image_id=$1 volume=$2
    docker run --rm --pull=never --network=none --read-only --cap-drop=ALL \
        --security-opt=no-new-privileges \
        --mount "type=volume,src=$volume,dst=/app/staticfiles,readonly" \
        --entrypoint python "$image_id" -B /app/EatHub/static_integrity.py /app/staticfiles
}

capture_static_manifest() {
    local image_id=$1 volume=$2 summary
    summary="$(calculate_static_manifest "$image_id" "$volume")" || return 1
    parse_static_manifest "$summary"
}

verify_static_manifest() {
    local image_id=$1 volume=$2 expected_algorithm=$3 expected_files=$4 expected_bytes=$5 expected_sha256=$6
    capture_static_manifest "$image_id" "$volume" || return 1
    [[ $STATIC_MANIFEST_ALGORITHM == "$expected_algorithm" &&
        $STATIC_MANIFEST_FILES == "$expected_files" &&
        $STATIC_MANIFEST_BYTES == "$expected_bytes" &&
        $STATIC_MANIFEST_SHA256 == "$expected_sha256" ]]
}

write_active_pointer() {
    local release_id=$1
    atomic_record "$STATE_DIR/current-successful-release" "$release_id"
}

verify_compose_service_image() {
    local expected=$1 service=$2 include_stopped=${3:-no} container_ids actual
    shift 3
    if [[ $include_stopped == yes ]]; then
        container_ids="$("$@" ps --all --quiet "$service")" || return 1
    else
        container_ids="$("$@" ps --quiet "$service")" || return 1
    fi
    [[ -n $container_ids && $container_ids != *$'\n'* ]] || return 1
    actual="$(docker inspect --format '{{.Image}}' "$container_ids")" || return 1
    [[ $actual == "$expected" ]]
}

verify_runtime_images() {
    local backend_id=$1 frontend_id=$2
    verify_compose_service_image "$backend_id" backend no "${compose_base[@]}" &&
        verify_compose_service_image "$frontend_id" frontend no "${compose_base[@]}" &&
        verify_compose_service_image "$backend_id" celery no "${compose_base[@]}"
}

verify_compose_static_mount() {
    local volume=$1 writable=$2 service=$3 include_stopped=${4:-no} container_id mount
    shift 4
    if [[ $include_stopped == yes ]]; then
        container_id="$("$@" ps --all --quiet "$service")" || return 1
    else
        container_id="$("$@" ps --quiet "$service")" || return 1
    fi
    [[ -n $container_id && $container_id != *$'\n'* ]] || return 1
    mount="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/app/staticfiles"}}{{.Name}}:{{.RW}}{{end}}{{end}}' "$container_id")" || return 1
    [[ $mount == "$volume:$writable" ]]
}

verify_collector_static_mount() {
    verify_compose_static_mount "$STATIC_VOLUME" true static-collector yes "${compose_release[@]}"
}

verify_nginx_static_mount() {
    verify_compose_static_mount "$STATIC_VOLUME" false nginx no "${compose_base[@]}"
}

check_clean_build_context() {
    CURRENT_STAGE=source-check
    local relevant_paths=(deployment/docker-compose.yml deployment/docker-compose.release.yml deployment/docker-compose.rollback.yml deployment/nginx/default.conf deployment/release.sh deployment/tests/test_release.sh deployment/STATIC_ASSETS.md)
    local path
    for path in deployment/docker-compose.yml deployment/docker-compose.release.yml deployment/docker-compose.rollback.yml deployment/nginx/default.conf deployment/release.sh deployment/tests/test_release.sh deployment/STATIC_ASSETS.md; do
        git -C "$REPO_ROOT" diff --quiet HEAD -- "$path" || die 'release source/configuration differs from HEAD; deploy a reviewed commit'
    done
    while IFS= read -r -d '' path; do
        case "$path" in
            backend/db.sqlite3|backend/media/*|*/.env|*/.env.*|*.pyc|*.pyo|*.pyd) continue ;;
        esac
        git -C "$REPO_ROOT" diff --quiet HEAD -- "$path" || die 'backend/frontend source differs from HEAD; deploy a reviewed commit'
    done < <(git -C "$REPO_ROOT" ls-files -z -- backend frontend)
    local extra
    extra="$(git -C "$REPO_ROOT" ls-files --others --exclude-standard -- "${relevant_paths[@]}")"
    [[ -z $extra ]] || die 'release source/configuration contains untracked files; deploy a reviewed commit'
    extra="$(git -C "$REPO_ROOT" ls-files --others --exclude-standard -- backend frontend)"
    [[ -z $extra ]] || die 'backend/frontend contain untracked build-context files; deploy a reviewed commit'
}

validate_compose_support() {
    local up_help
    CURRENT_STAGE=compose-compatibility
    up_help="$(docker compose up --help 2>/dev/null)" || die 'cannot inspect Docker Compose up capabilities'
    [[ $up_help == *--no-build* && $up_help == *--pull* ]] || die 'Compose up lacks required --no-build/--pull options'
}

validate_release_topology() {
    local release_services runtime_services
    release_services="$("${compose_release[@]}" config --services 2>"$STATE_DIR/compose-release-config.log")" || die 'release Compose configuration is invalid'
    runtime_services="$("${compose_base[@]}" config --services 2>"$STATE_DIR/compose-runtime-config.log")" || die 'runtime Compose configuration is invalid'
    grep -qx 'static-collector' <<< "$release_services" || die 'release Compose model does not contain static-collector'
    if grep -qx 'static-collector' <<< "$runtime_services"; then die 'runtime Compose model unexpectedly contains static-collector'; fi
}

validate_rollback_topology() {
    local rollback_services
    rollback_services="$("${compose_rollback[@]}" config --services 2>"$STATE_DIR/compose-rollback-config.log")" || die 'rollback Compose configuration is invalid'
    if grep -qx 'static-collector' <<< "$rollback_services"; then die 'rollback Compose model contains static-collector'; fi
    [[ -n $rollback_services ]] || die 'rollback Compose model has no services'
}

compose_base=(docker compose -f "$BASE_FILE")
compose_release=(docker compose -f "$BASE_FILE" -f "$RELEASE_FILE")
compose_rollback=(docker compose -f "$BASE_FILE" -f "$ROLLBACK_FILE")

preflight_common() {
    DEPLOYMENT_NAMESPACE=${DEPLOYMENT_NAMESPACE:-}
    [[ -n $DEPLOYMENT_NAMESPACE ]] && valid_namespace "$DEPLOYMENT_NAMESPACE" || die 'DEPLOYMENT_NAMESPACE must be a lowercase slug of at most 40 characters'
    export DEPLOYMENT_NAMESPACE
    [[ -n ${EATHUB_RELEASE_STATE_DIR:-} ]] || die 'EATHUB_RELEASE_STATE_DIR is required'
    prepare_state_dir
    trap finish_operation EXIT
    command -v docker >/dev/null || die 'docker CLI is unavailable'
    command -v git >/dev/null || die 'git is unavailable'
    docker info >/dev/null 2>&1 || die 'Docker Engine is unavailable'
    docker compose version >/dev/null 2>&1 || die 'Docker Compose is unavailable'
    validate_compose_support
}

do_release() {
    [[ $# == 1 ]] || die 'usage: release.sh release <attempt-id>'
    ATTEMPT_ID=$1
    valid_attempt_id "$ATTEMPT_ID" || die 'attempt ID format is invalid'
    require_compose_database_inputs
    require_release_specific_readiness || die 'set EATHUB_READINESS_URL to the local Nginx HTTPS origin and ensure curl is available'
    preflight_common
    attempt_is_unused "$ATTEMPT_ID" || die 'attempt ID has already been used'
    ATTEMPT_RECORD="$(attempt_record_path "$ATTEMPT_ID")"
    ATTEMPT_FINALIZED=0
    OPERATION_ID="attempt-$ATTEMPT_ID"
    BACKEND_TAG="$(backend_tag_for "$DEPLOYMENT_NAMESPACE" "$ATTEMPT_ID")"
    FRONTEND_TAG="$(frontend_tag_for "$DEPLOYMENT_NAMESPACE" "$ATTEMPT_ID")"
    STATIC_VOLUME="$(static_volume_for "$DEPLOYMENT_NAMESPACE" "$ATTEMPT_ID")"
    SOURCE_REVISION="$(git -C "$REPO_ROOT" rev-parse HEAD)" || die 'cannot resolve source revision'
    attempt_matches_source_revision "$ATTEMPT_ID" "$SOURCE_REVISION" || die 'attempt ID revision prefix does not match the source revision'
    EXPECTED_RELEASE_ID="success-$ATTEMPT_ID"
    export DEPLOYMENT_NAMESPACE STATIC_ASSET_ATTEMPT="$ATTEMPT_ID"
    BACKEND_IMAGE_ID=''
    FRONTEND_IMAGE_ID=''
    write_attempt_state started preflight

    [[ ${VITE_API_BASE_URL:-} != '' && ${VITE_BASE_URL:-} != '' ]] || die 'public VITE_API_BASE_URL and VITE_BASE_URL must be provided in the process environment'
    check_clean_build_context
    validate_release_topology
    if docker image inspect "$BACKEND_TAG" >/dev/null 2>&1 || docker image inspect "$FRONTEND_TAG" >/dev/null 2>&1; then
        die 'attempt-specific image tag already exists; use a new attempt ID'
    fi
    if docker volume inspect "$STATIC_VOLUME" >/dev/null 2>&1; then
        die 'attempt-specific static volume already exists; use a new attempt ID'
    fi

    CURRENT_STAGE=build
    run_logged build "${compose_release[@]}" build backend frontend
    BACKEND_IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$BACKEND_TAG")" || die 'built backend image cannot be inspected'
    FRONTEND_IMAGE_ID="$(docker image inspect --format '{{.Id}}' "$FRONTEND_TAG")" || die 'built frontend image cannot be inspected'
    [[ $BACKEND_IMAGE_ID =~ ^sha256:[0-9a-f]{64}$ && $FRONTEND_IMAGE_ID =~ ^sha256:[0-9a-f]{64}$ ]] || die 'image inspection returned an unexpected local image ID'
    assert_image_tag_id "$BACKEND_TAG" "$BACKEND_IMAGE_ID" || die 'backend image tag changed after build'
    assert_image_tag_id "$FRONTEND_TAG" "$FRONTEND_IMAGE_ID" || die 'frontend image tag changed after build'
    assert_frontend_release_id "$FRONTEND_TAG" "$EXPECTED_RELEASE_ID" || die 'frontend image does not contain the expected release identity'
    write_attempt_state collecting collector

    assert_image_tag_id "$BACKEND_TAG" "$BACKEND_IMAGE_ID" || die 'backend image tag changed before collection'
    run_logged collector "${compose_release[@]}" up --no-deps --no-build --pull never static-collector
    verify_compose_service_image "$BACKEND_IMAGE_ID" static-collector yes "${compose_release[@]}" || die 'collector did not run the recorded backend image'
    verify_collector_static_mount || die 'collector did not mount the new static volume read-write'
    capture_static_manifest "$BACKEND_IMAGE_ID" "$STATIC_VOLUME" || die 'collected static volume is empty, malformed, or cannot be verified'
    write_attempt_state collected static-manifest-verified
    write_attempt_state deploying deploy
    assert_image_tag_id "$BACKEND_TAG" "$BACKEND_IMAGE_ID" || die 'backend image tag changed before activation'
    assert_image_tag_id "$FRONTEND_TAG" "$FRONTEND_IMAGE_ID" || die 'frontend image tag changed before activation'
    run_logged deploy "${compose_base[@]}" up -d --no-build --pull never
    verify_runtime_images "$BACKEND_IMAGE_ID" "$FRONTEND_IMAGE_ID" || die 'activated backend, frontend, or Celery container uses an unexpected image ID'
    verify_nginx_static_mount || die 'Nginx is not using the expected static volume read-only'
    check_readiness "$EXPECTED_RELEASE_ID" || die 'local HTTPS readiness did not report the expected release identity'
    verify_static_manifest "$BACKEND_IMAGE_ID" "$STATIC_VOLUME" \
        "$STATIC_MANIFEST_ALGORITHM" "$STATIC_MANIFEST_FILES" "$STATIC_MANIFEST_BYTES" "$STATIC_MANIFEST_SHA256" ||
        die 'static volume contents changed after collection or activation'

    local release_id release_record
    release_id=$EXPECTED_RELEASE_ID
    release_record="$(release_record_path "$release_id")"
    [[ ! -e $release_record ]] || die 'successful release record already exists; refusing to overwrite it'
    atomic_record "$release_record" \
        'format=1' 'status=successful' "release_id=$release_id" \
        "namespace=$DEPLOYMENT_NAMESPACE" "source_revision=$SOURCE_REVISION" \
        "attempt_id=$ATTEMPT_ID" "backend_image_tag=$BACKEND_TAG" \
        "backend_image_id=$BACKEND_IMAGE_ID" "frontend_image_tag=$FRONTEND_TAG" \
        "frontend_image_id=$FRONTEND_IMAGE_ID" "static_volume_name=$STATIC_VOLUME" \
        "static_manifest_algorithm=$STATIC_MANIFEST_ALGORITHM" \
        "static_manifest_files=$STATIC_MANIFEST_FILES" \
        "static_manifest_bytes=$STATIC_MANIFEST_BYTES" \
        "static_manifest_sha256=$STATIC_MANIFEST_SHA256" \
        "deployment_timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        'verification_status=passed'
    ATTEMPT_FINALIZED=1
    if ! write_attempt_state successful complete passed; then
        printf 'WARNING: release record is authoritative, but the attempt record could not be finalized.\n' >&2
    fi
    if ! write_active_pointer "$release_id"; then
        printf 'WARNING: release succeeded, but the advisory active-release pointer could not be updated.\n' >&2
    fi
    printf 'Release %s verified and recorded.\n' "$release_id"
}

do_rollback() {
    [[ $# == 1 ]] || die 'usage: release.sh rollback <successful-release-id>'
    TARGET_RELEASE_ID=$1
    valid_release_id "$TARGET_RELEASE_ID" || die 'successful release ID format is invalid'
    require_compose_database_inputs
    require_release_specific_readiness || die 'set EATHUB_READINESS_URL to the local Nginx HTTPS origin and ensure curl is available'
    preflight_common
    local record namespace attempt source_revision backend_tag frontend_tag backend_id frontend_id volume manifest_algorithm manifest_files manifest_bytes manifest_sha256
    record="$(release_record_path "$TARGET_RELEASE_ID")"
    record_is_successful "$record" "$TARGET_RELEASE_ID" || die 'target release record is malformed or not a verified successful release'
    namespace="$(record_value "$record" namespace)"
    [[ $namespace == "$DEPLOYMENT_NAMESPACE" ]] || die 'release belongs to a different deployment namespace'
    attempt="$(record_value "$record" attempt_id)"
    valid_attempt_id "$attempt" || die 'release record has an invalid attempt ID'
    source_revision="$(record_value "$record" source_revision)"
    attempt_matches_source_revision "$attempt" "$source_revision" || die 'release record attempt ID does not match its source revision'
    backend_tag="$(record_value "$record" backend_image_tag)"
    frontend_tag="$(record_value "$record" frontend_image_tag)"
    backend_id="$(record_value "$record" backend_image_id)"
    frontend_id="$(record_value "$record" frontend_image_id)"
    volume="$(record_value "$record" static_volume_name)"
    manifest_algorithm="$(record_value "$record" static_manifest_algorithm)"
    manifest_files="$(record_value "$record" static_manifest_files)"
    manifest_bytes="$(record_value "$record" static_manifest_bytes)"
    manifest_sha256="$(record_value "$record" static_manifest_sha256)"
    [[ $backend_tag == "$(backend_tag_for "$namespace" "$attempt")" && $frontend_tag == "$(frontend_tag_for "$namespace" "$attempt")" ]] || die 'record image tags do not match the namespace and attempt'
    [[ $volume == "$(static_volume_for "$namespace" "$attempt")" ]] || die 'record static volume does not match the namespace and attempt'
    [[ $backend_id =~ ^sha256:[0-9a-f]{64}$ && $frontend_id =~ ^sha256:[0-9a-f]{64}$ ]] || die 'release record has invalid image IDs'
    export STATIC_ASSET_ATTEMPT="$attempt"
    validate_rollback_topology

    OPERATION_ID="rollback-$(date -u +%Y%m%dt%H%M%Sz)-$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')"
    local candidate_rollback_record="$STATE_DIR/$OPERATION_ID.record"
    [[ ! -e $candidate_rollback_record ]] || die 'rollback operation record collision; retry after operator review'
    ROLLBACK_RECORD=$candidate_rollback_record
    ROLLBACK_FINALIZED=0
    atomic_record "$ROLLBACK_RECORD" 'format=1' 'status=started' "release_id=$TARGET_RELEASE_ID" \
        "started_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

    verify_recorded_artifacts "$backend_tag" "$backend_id" "$frontend_tag" "$frontend_id" "$TARGET_RELEASE_ID" "$volume" || die 'recorded image or matching static volume is not available with the expected identity'
    STATIC_VOLUME=$volume
    verify_static_manifest "$backend_id" "$STATIC_VOLUME" "$manifest_algorithm" "$manifest_files" "$manifest_bytes" "$manifest_sha256" ||
        die 'recorded static volume is empty, malformed, or does not match its release manifest'

    CURRENT_STAGE=rollback
    run_logged rollback "${compose_rollback[@]}" up -d --no-build --pull never
    verify_runtime_images "$backend_id" "$frontend_id" || die 'rollback activated a backend, frontend, or Celery container with an unexpected image ID'
    verify_nginx_static_mount || die 'rollback Nginx is not using the recorded static volume read-only'
    check_readiness "$TARGET_RELEASE_ID" || die 'local HTTPS readiness did not report the rollback release identity'
    verify_static_manifest "$backend_id" "$STATIC_VOLUME" "$manifest_algorithm" "$manifest_files" "$manifest_bytes" "$manifest_sha256" ||
        die 'static volume contents changed during rollback activation'
    atomic_record "$ROLLBACK_RECORD" 'format=1' 'status=successful' "release_id=$TARGET_RELEASE_ID" \
        "verification_status=passed" "completed_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    ROLLBACK_FINALIZED=1
    if ! write_active_pointer "$TARGET_RELEASE_ID"; then
        printf 'WARNING: rollback succeeded, but the advisory active-release pointer could not be updated.\n' >&2
    fi
    printf 'Rollback to %s verified. No image build, collection, or artifact deletion was performed.\n' "$TARGET_RELEASE_ID"
}

main() {
    local action=${1:-}
    shift || true
    case "$action" in
        release) do_release "$@" ;;
        rollback) do_rollback "$@" ;;
        *) die 'usage: release.sh {release <attempt-id>|rollback <successful-release-id>}' ;;
    esac
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then main "$@"; fi
