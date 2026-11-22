"""Tenant-scoped, lock-aware read access for refund recovery."""

from products.models import Order, OrderRefund


class DjangoOrderRefundReadRepository:
    """Read a completed refund receipt while preserving the order row lock.

    The caller owns the surrounding transaction.atomic() block. The order
    lock is intentional: refund creation locks the same order before changing
    its payment state, so recovery must wait for an in-flight refund commit.
    Refund rows are materialized without adding a new row lock, matching the
    existing GET behavior.
    """

    def get_recovery_state_for_business(self, business_id, order_id):
        order = (
            Order.objects.select_for_update()
            .filter(pk=order_id, business_id=business_id)
            .first()
        )
        if order is None:
            return None, []

        refunds = list(
            OrderRefund.objects.filter(
                order_id=order.pk,
                business_id=business_id,
            ).order_by("pk")
        )
        return order, refunds
