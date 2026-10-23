#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
source "$SCRIPT_DIR/../release.sh"

test_root="$(mktemp -d "${TMPDIR:-/tmp}/eathub-release-test.XXXXXX")"
STATE_DIR="$test_root/state"
mkdir -m 700 -- "$STATE_DIR"
cleanup() {
    rm -f -- "$STATE_DIR"/* "$STATE_DIR"/.[!.]* 2>/dev/null || true
    rm -f -- "$test_root"/wrapper-stdout "$test_root"/wrapper-stderr
    rmdir -- "$STATE_DIR" "$test_root"
}
trap cleanup EXIT

assert_ok() {
    if ! "$@"; then
        printf 'assertion failed: %s\n' "$*" >&2
        exit 1
    fi
}

assert_fail() {
    if "$@"; then
        printf 'unexpected success: %s\n' "$*" >&2
        exit 1
    fi
}

attempt='20261022t010203z-0123456789ab-abcdef01'
namespace='eathub-production'
backend_id="sha256:$(printf '%064d' 1)"
frontend_id="sha256:$(printf '%064d' 2)"
other_id="sha256:$(printf '%064d' 3)"
backend_tag="$(backend_tag_for "$namespace" "$attempt")"
frontend_tag="$(frontend_tag_for "$namespace" "$attempt")"
volume="$(static_volume_for "$namespace" "$attempt")"
timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
manifest_sha256="$(printf '%064d' 4)"
static_manifest_summary="algorithm=eathub-static-manifest-v1
files=2
bytes=9
sha256=$manifest_sha256"

assert_ok valid_namespace "$namespace"
assert_fail valid_namespace 'Bad_namespace'
assert_ok valid_attempt_id "$attempt"
assert_fail valid_attempt_id '20261399t256199z-0123456789ab-abcdef01'
assert_ok valid_release_id "success-$attempt"
assert_fail valid_release_id "failed-$attempt"
source_revision="${attempt:17:12}$(printf '%028d' 0)"
assert_ok attempt_matches_source_revision "$attempt" "$source_revision"
assert_fail attempt_matches_source_revision "$attempt" "ffffffffffff$(printf '%028d' 0)"

MOCK_READINESS_HOST='eathub.ir'
MOCK_READINESS_BODY="ready:success-$attempt"
MOCK_CURL_FAILURE=0
MOCK_READINESS_CALLS=0
MOCK_READY_AFTER=1
sleep() { :; }
curl() {
    local args="$*"
    [[ $args == *"--resolve $MOCK_READINESS_HOST:443:127.0.0.1"* ]] || return 1
    [[ ${!#} == "https://$MOCK_READINESS_HOST/api/ready/" ]] || return 1
    MOCK_READINESS_CALLS=$((MOCK_READINESS_CALLS + 1))
    (( MOCK_CURL_FAILURE == 0 )) || return 22
    (( MOCK_READINESS_CALLS >= MOCK_READY_AFTER )) || return 22
    printf '%s' "$MOCK_READINESS_BODY"
}
EATHUB_READINESS_URL="https://$MOCK_READINESS_HOST/"
assert_ok check_readiness "success-$attempt"
MOCK_READINESS_CALLS=0
MOCK_READY_AFTER=3
assert_ok check_readiness "success-$attempt"
[[ $MOCK_READINESS_CALLS == 3 ]]
MOCK_READINESS_CALLS=0
MOCK_READY_AFTER=1
MOCK_READINESS_BODY="ready:success-$attempt-other"
assert_fail check_readiness "success-$attempt"
MOCK_READINESS_BODY="ready:success-$attempt"
MOCK_CURL_FAILURE=1
assert_fail check_readiness "success-$attempt"
MOCK_CURL_FAILURE=0
EATHUB_READINESS_URL='http://eathub.ir'
assert_fail check_readiness "success-$attempt"
EATHUB_READINESS_URL="https://$MOCK_READINESS_HOST/"

assert_ok attempt_is_unused "$attempt"
attempt_file="$(attempt_record_path "$attempt")"
atomic_record "$attempt_file" 'format=1' 'status=failed' "attempt_id=$attempt"
assert_fail attempt_is_unused "$attempt"

release_id="success-$attempt"
release_file="$(release_record_path "$release_id")"
write_valid_release_record() {
    atomic_record "$release_file" \
        'format=1' 'status=successful' "release_id=$release_id" \
        "namespace=$namespace" "source_revision=$source_revision" \
        "attempt_id=$attempt" "backend_image_tag=$backend_tag" \
        "backend_image_id=$backend_id" "frontend_image_tag=$frontend_tag" \
        "frontend_image_id=$frontend_id" "static_volume_name=$volume" \
        'static_manifest_algorithm=eathub-static-manifest-v1' \
        'static_manifest_files=2' 'static_manifest_bytes=9' \
        "static_manifest_sha256=$manifest_sha256" \
        "deployment_timestamp_utc=$timestamp" 'verification_status=passed'
}
write_valid_release_record
assert_ok record_is_successful "$release_file" "$release_id"
assert_fail record_is_successful "$release_file" 'success-20261022t010204z-0123456789ab-abcdef02'
source_revision="ffffffffffff$(printf '%028d' 0)"
write_valid_release_record
assert_fail record_is_successful "$release_file" "$release_id"
source_revision="${attempt:17:12}$(printf '%028d' 0)"
write_valid_release_record

atomic_record "$release_file" 'format=1' 'status=successful' "release_id=$release_id" \
    "namespace=$namespace" "source_revision=$source_revision" \
    "attempt_id=$attempt" "backend_image_tag=$backend_tag" \
    "backend_image_id=$backend_id" "frontend_image_tag=$frontend_tag" \
    "frontend_image_id=$frontend_id" "static_volume_name=$volume" \
    "deployment_timestamp_utc=$timestamp" 'verification_status=passed'
assert_fail record_is_successful "$release_file" "$release_id"
write_valid_release_record

atomic_record "$release_file" \
    'format=1' 'status=successful' "release_id=$release_id" \
    "namespace=$namespace" "source_revision=$source_revision" \
    "attempt_id=$attempt" "backend_image_tag=$backend_tag" \
    "backend_image_id=$backend_id" "frontend_image_tag=$frontend_tag" \
    "frontend_image_id=$frontend_id" "static_volume_name=$volume" \
    'static_manifest_algorithm=eathub-static-manifest-v1' \
    'static_manifest_files=2' 'static_manifest_bytes=9' \
    "deployment_timestamp_utc=$timestamp" 'verification_status=passed'
assert_fail record_is_successful "$release_file" "$release_id"
write_valid_release_record

atomic_record "$release_file" \
    'format=1' 'status=successful' "release_id=$release_id" \
    "namespace=$namespace" "source_revision=$source_revision" \
    "attempt_id=$attempt" "backend_image_tag=$backend_tag" \
    "backend_image_id=$backend_id" "frontend_image_tag=$frontend_tag" \
    "frontend_image_id=$frontend_id" "static_volume_name=$volume" \
    'static_manifest_algorithm=eathub-static-manifest-v1' \
    'static_manifest_files=0' 'static_manifest_bytes=9' \
    "static_manifest_sha256=$manifest_sha256" \
    "deployment_timestamp_utc=$timestamp" 'verification_status=passed'
assert_fail record_is_successful "$release_file" "$release_id"
write_valid_release_record

atomic_record "$release_file" \
    'format=1' 'status=successful' "release_id=$release_id" \
    "namespace=$namespace" "source_revision=$source_revision" \
    "attempt_id=$attempt" "backend_image_tag=$backend_tag" \
    "backend_image_id=$backend_id" "frontend_image_tag=$frontend_tag" \
    "frontend_image_id=$frontend_id" "static_volume_name=$volume" \
    'static_manifest_algorithm=eathub-static-manifest-v1' \
    'static_manifest_files=2' 'static_manifest_bytes=9' \
    'static_manifest_sha256=malformed' \
    "deployment_timestamp_utc=$timestamp" 'verification_status=passed'
assert_fail record_is_successful "$release_file" "$release_id"
write_valid_release_record
atomic_record "$release_file" \
    'format=1' 'status=successful' "release_id=$release_id" \
    "namespace=$namespace" "source_revision=$source_revision" \
    "attempt_id=$attempt" "backend_image_tag=$backend_tag" \
    "backend_image_id=$backend_id" "frontend_image_tag=$frontend_tag" \
    "frontend_image_id=$frontend_id" "static_volume_name=$volume" \
    "deployment_timestamp_utc=$timestamp" 'verification_status=passed' 'unexpected=value'
assert_fail record_is_successful "$release_file" "$release_id"
write_valid_release_record

declare -A MOCK_TAG_IDS=(["$backend_tag"]="$backend_id" ["$frontend_tag"]="$frontend_id")
declare -A MOCK_TAG_RELEASE_IDS=(["$frontend_tag"]="$release_id")
declare -A MOCK_CONTAINER_IDS=([backend]='container-backend' [frontend]='container-frontend' [celery]='container-celery' [static-collector]='container-collector' [nginx]='container-nginx')
declare -A MOCK_CONTAINER_IMAGES=([container-backend]="$backend_id" [container-frontend]="$frontend_id" [container-celery]="$backend_id" [container-collector]="$backend_id" [container-nginx]='sha256:nginx')
declare -A MOCK_CONTAINER_MOUNTS=([container-collector]="$volume:true" [container-nginx]="$volume:false")
MOCK_VOLUME_EXISTS=1
docker() {
    if [[ $1 == run ]]; then
        [[ ${MOCK_STATIC_MANIFEST_FAILURE:-0} == 0 ]] || return 1
        printf '%s\n' "$MOCK_STATIC_MANIFEST"
    elif [[ $1 == image && $2 == inspect ]]; then
        local tag=${@: -1}
        [[ -n ${MOCK_TAG_IDS[$tag]:-} ]] || return 1
        if [[ ${4:-} == *'com.eathub.release-id'* ]]; then
            [[ -n ${MOCK_TAG_RELEASE_IDS[$tag]:-} ]] || return 1
            printf '%s\n' "${MOCK_TAG_RELEASE_IDS[$tag]}"
        else
            printf '%s\n' "${MOCK_TAG_IDS[$tag]}"
        fi
    elif [[ $1 == volume && $2 == inspect ]]; then
        (( MOCK_VOLUME_EXISTS == 1 ))
    elif [[ $1 == inspect && $2 == --format ]]; then
        local format=$3 container=$4
        if [[ $format == '{{.Image}}' ]]; then
            [[ -n ${MOCK_CONTAINER_IMAGES[$container]:-} ]] || return 1
            printf '%s\n' "${MOCK_CONTAINER_IMAGES[$container]}"
        elif [[ -n ${MOCK_CONTAINER_MOUNTS[$container]:-} ]]; then
            printf '%s\n' "${MOCK_CONTAINER_MOUNTS[$container]}"
        else
            return 1
        fi
    elif [[ $1 == compose ]]; then
        local service=${@: -1}
        [[ -n ${MOCK_CONTAINER_IDS[$service]:-} ]] || return 1
        printf '%s\n' "${MOCK_CONTAINER_IDS[$service]}"
    else
        return 1
    fi
}

assert_ok assert_image_tag_id "$backend_tag" "$backend_id"
MOCK_TAG_IDS["$backend_tag"]=$other_id
assert_fail assert_image_tag_id "$backend_tag" "$backend_id"
MOCK_TAG_IDS["$backend_tag"]=$backend_id

compose_base=(docker compose -f mock-compose.yml)
compose_release=(docker compose -f mock-compose.yml -f mock-release.yml)
assert_ok verify_compose_service_image "$backend_id" static-collector yes "${compose_release[@]}"
MOCK_CONTAINER_IMAGES[container-collector]=$other_id
assert_fail verify_compose_service_image "$backend_id" static-collector yes "${compose_release[@]}"
MOCK_CONTAINER_IMAGES[container-collector]=$backend_id
assert_ok verify_collector_static_mount
MOCK_CONTAINER_MOUNTS[container-collector]='wrong-volume:true'
assert_fail verify_collector_static_mount
MOCK_CONTAINER_MOUNTS[container-collector]="$volume:true"

assert_ok verify_runtime_images "$backend_id" "$frontend_id"
MOCK_CONTAINER_IMAGES[container-celery]=$other_id
assert_fail verify_runtime_images "$backend_id" "$frontend_id"
MOCK_CONTAINER_IMAGES[container-celery]=$backend_id
assert_ok verify_nginx_static_mount
MOCK_CONTAINER_MOUNTS[container-nginx]='another-volume:false'
assert_fail verify_nginx_static_mount
MOCK_CONTAINER_MOUNTS[container-nginx]="$volume:false"

assert_ok verify_recorded_artifacts "$backend_tag" "$backend_id" "$frontend_tag" "$frontend_id" "$release_id" "$volume"
assert_fail verify_recorded_artifacts "$backend_tag" "$other_id" "$frontend_tag" "$frontend_id" "$release_id" "$volume"
MOCK_TAG_RELEASE_IDS["$frontend_tag"]='success-different-release'
assert_fail verify_recorded_artifacts "$backend_tag" "$backend_id" "$frontend_tag" "$frontend_id" "$release_id" "$volume"
MOCK_TAG_RELEASE_IDS["$frontend_tag"]=$release_id
MOCK_VOLUME_EXISTS=0
assert_fail verify_recorded_artifacts "$backend_tag" "$backend_id" "$frontend_tag" "$frontend_id" "$release_id" "$volume"
MOCK_VOLUME_EXISTS=1

MOCK_STATIC_MANIFEST="$static_manifest_summary"
MOCK_STATIC_MANIFEST_FAILURE=0
assert_ok verify_static_manifest "$backend_id" "$volume" eathub-static-manifest-v1 2 9 "$manifest_sha256"
assert_fail verify_static_manifest "$backend_id" "$volume" eathub-static-manifest-v1 2 9 "$(printf '%064d' 5)"
MOCK_STATIC_MANIFEST='algorithm=eathub-static-manifest-v1
files=0
bytes=9
sha256='"$manifest_sha256"
assert_fail verify_static_manifest "$backend_id" "$volume" eathub-static-manifest-v1 2 9 "$manifest_sha256"
MOCK_STATIC_MANIFEST=''
MOCK_STATIC_MANIFEST_FAILURE=1
assert_fail verify_static_manifest "$backend_id" "$volume" eathub-static-manifest-v1 2 9 "$manifest_sha256"

assert_fail check_readiness 'success-invalid'
EATHUB_READINESS_URL='not-an-https-origin'
assert_fail require_release_specific_readiness
EATHUB_READINESS_URL="https://$MOCK_READINESS_HOST/"
assert_ok require_release_specific_readiness
blocked_state="$test_root/blocked-state"
if DEPLOYMENT_NAMESPACE="$namespace" DB_NAME=test DB_USER=test DB_PASSWORD=test-only-placeholder \
    EATHUB_READINESS_URL='not-an-https-origin' EATHUB_RELEASE_STATE_DIR="$blocked_state" \
    bash "$SCRIPT_DIR/../release.sh" release "$attempt" \
    >"$test_root/wrapper-stdout" 2>"$test_root/wrapper-stderr"; then
    printf 'release wrapper did not fail closed without release-specific readiness\n' >&2
    exit 1
fi
grep -q 'set EATHUB_READINESS_URL' "$test_root/wrapper-stderr"
[[ ! -e $blocked_state ]]
if DEPLOYMENT_NAMESPACE="$namespace" DB_NAME=test DB_USER=test DB_PASSWORD=test-only-placeholder \
    EATHUB_READINESS_URL='not-an-https-origin' EATHUB_RELEASE_STATE_DIR="$blocked_state" \
    bash "$SCRIPT_DIR/../release.sh" rollback "success-$attempt" \
    >"$test_root/wrapper-stdout" 2>"$test_root/wrapper-stderr"; then
    printf 'rollback wrapper did not fail closed without release-specific readiness\n' >&2
    exit 1
fi
grep -q 'set EATHUB_READINESS_URL' "$test_root/wrapper-stderr"
[[ ! -e $blocked_state ]]
OPERATION_ID='test-collection-failure'
if run_logged collection false; then
    printf 'failed collection command was incorrectly accepted\n' >&2
    exit 1
fi
[[ -f "$STATE_DIR/$OPERATION_ID-collection.log" ]]

mv() { return 1; }
assert_fail write_active_pointer "$release_id"
unset -f mv

printf 'PASS: release safety helper tests\n'
