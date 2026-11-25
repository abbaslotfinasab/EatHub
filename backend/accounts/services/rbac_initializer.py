"""Backward-compatible import path; implementation lives in Infrastructure."""

from accounts.infrastructure.django.rbac_initializer import (
    DjangoRBACInitializer as RBACInitializer,
    ROLE_PERMISSIONS,
)

__all__ = ["RBACInitializer", "ROLE_PERMISSIONS"]
