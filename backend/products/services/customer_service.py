"""Backward-compatible import path for the Customer application service.

New code should import CustomerService from customer.services.
"""

from customer.services.customer_service import CustomerService

__all__ = ["CustomerService"]
