"""Django-backed read queries for customer wallet accounts."""

from customer.models import Customer
from financial.models import CustomerAccount


class DjangoCustomerAccountReadRepository:
    """Own tenant-scoped Customer and wallet-account reads."""

    def get_account_for_business(self, business_id, customer_id):
        return (
            CustomerAccount.objects.select_related("customer")
            .filter(customer_id=customer_id, business_id=business_id)
            .first()
        )

    def get_customer_for_business(self, business_id, customer_id):
        return Customer.objects.filter(
            pk=customer_id,
            business_id=business_id,
        ).first()

    def list_transactions_for_account(self, account):
        return account.transactions.all().order_by("-id")
