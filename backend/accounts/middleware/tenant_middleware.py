from django.http import HttpResponseForbidden
from accounts.models import Membership

TENANT_EXEMPT_PATHS = [
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/me",
]

class TenantMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        path = request.path

        # 🔥 skip tenant logic for public endpoints
        if any(path.startswith(p) for p in TENANT_EXEMPT_PATHS):
            return self.get_response(request)

        request.business = None
        request.membership = None
        request.role = None
        request.permissions = []

        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return self.get_response(request)

        business_id = request.headers.get("X-Business-Id")

        if not business_id:
            # 🔥 fallback: first active membership
            membership = (
                Membership.objects
                .select_related("business", "role")
                .filter(user=user, is_active=True)
                .first()
            )

            if not membership:
                return self.get_response(request)

        else:
            try:
                membership = Membership.objects.select_related(
                    "business",
                    "role"
                ).get(
                    user=user,
                    business_id=business_id,
                    is_active=True
                )
            except Membership.DoesNotExist:
                return HttpResponseForbidden("Invalid business access")

        request.business = membership.business
        request.membership = membership
        request.role = membership.role

        # 🔥 permissions attach (important for RBAC)
        request.permissions = list(
            membership.role.permissions.values_list(
                "code",
                flat=True
            )
        )

        return self.get_response(request)