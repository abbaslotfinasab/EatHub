# accounts/constants.py


# -----------------------------
# Role / RBAC
# -----------------------------

from typing import Final


class SystemRoles:
    OWNER: Final = "OWNER"
    MANAGER: Final = "MANAGER"
    CASHIER: Final = "CASHIER"
    CHEF: Final = "CHEF"
    WAITER: Final = "WAITER"
    ACCOUNTANT: Final = "ACCOUNTANT"


# استفاده در RBACInitializer برای Owner (دسترسی کامل)
ALL_PERMISSIONS = object()


# -----------------------------
# Business / Tenant
# -----------------------------

DEFAULT_TIMEZONE: Final = "Asia/Tehran"
DEFAULT_CURRENCY: Final = "IRR"


# -----------------------------
# Invitation
# -----------------------------

INVITATION_TOKEN_LENGTH: Final = 32  # future use if needed
INVITATION_EXPIRATION_DAYS: Final = 7


# -----------------------------
# User
# -----------------------------

MIN_PASSWORD_LENGTH: Final = 8


# -----------------------------
# Membership
# -----------------------------

class MembershipStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


# -----------------------------
# Permissions domains (optional helper)
# فقط برای نظم دادن به codeها
# -----------------------------

class PermissionDomains:
    ORDERS = "orders"
    PRODUCTS = "products"
    INVENTORY = "inventory"
    REPORTS = "reports"
    EMPLOYEES = "employees"
    SETTINGS = "settings"


# -----------------------------
# Common Errors (future use in services)
# -----------------------------

class ErrorCodes:
    USER_ALREADY_EXISTS = "user_already_exists"
    INVALID_CREDENTIALS = "invalid_credentials"
    BUSINESS_NOT_FOUND = "business_not_found"
    PERMISSION_DENIED = "permission_denied"