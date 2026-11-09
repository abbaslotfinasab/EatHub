from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def release_readiness(request):
    """Report whether this process can serve traffic backed by the database."""
    try:
        connection.ensure_connection()
    except DatabaseError:
        response = JsonResponse(
            {"status": "not_ready", "checks": {"database": "error"}},
            status=503,
        )
    else:
        response = JsonResponse(
            {"status": "ready", "checks": {"database": "ok"}},
            status=200,
        )

    response["Cache-Control"] = "no-store"
    return response
