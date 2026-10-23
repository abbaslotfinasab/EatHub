import os
import re
from datetime import datetime

from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


_RELEASE_ID_PATTERN = re.compile(
    r"^success-(\d{8})t(\d{6})z-[0-9a-f]{12}-[0-9a-f]{8}$"
)


def _configured_release_id():
    release_id = os.environ.get("EATHUB_RELEASE_ID", "")
    match = _RELEASE_ID_PATTERN.fullmatch(release_id)
    if match is None:
        return None

    try:
        datetime.strptime(
            f"{match.group(1)}T{match.group(2)}Z", "%Y%m%dT%H%M%SZ"
        )
    except ValueError:
        return None

    return release_id


@never_cache
@require_GET
def release_readiness(request):
    release_id = _configured_release_id()
    if release_id is None:
        response = JsonResponse({"status": "not_ready"}, status=503)
        response["Cache-Control"] = "no-store"
        return response

    response = HttpResponse(
        f"ready:{release_id}",
        content_type="text/plain; charset=utf-8",
    )
    response["Cache-Control"] = "no-store"
    return response
