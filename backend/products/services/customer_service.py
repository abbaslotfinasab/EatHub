from django.db import transaction
from rest_framework.exceptions import ValidationError

from products.models import Customer, CustomerAccount, CustomerTransaction, Order


class CustomerService:

    @staticmethod
    @transaction.atomic
    def create_customer(*, business, validated_data):

        customer, created = Customer.objects.get_or_create(
            business=business,
            phone=validated_data["phone"],
            defaults={
                "name": validated_data["name"],
            }
        )

        # اگر وجود داشت آپدیت اسم
        if not created:
            customer.name = validated_data["name"]
            customer.save(update_fields=["name"])

        return customer

    @staticmethod
    @transaction.atomic
    def update_customer(*, customer, validated_data):

        for key, value in validated_data.items():
            setattr(customer, key, value)

        customer.save()
        return customer



    @staticmethod
    @transaction.atomic
    def delete_customer(*, customer):
        # Match order-payment locking (orders before wallet accounts) and re-read
        # after locking the customer so a concurrent payment is not missed.
        list(
            Order.objects.select_for_update()
            .filter(customer_id=customer.pk)
            .order_by("pk")
        )
        customer = Customer.objects.select_for_update().get(pk=customer.pk)
        orders = list(
            Order.objects.select_for_update()
            .filter(customer=customer)
            .order_by("pk")
        )
        account = (
            CustomerAccount.objects.select_for_update()
            .filter(customer=customer)
            .first()
        )

        has_account_history = account is not None and (
            account.balance != 0 or account.transactions.exists()
        )
        # Any order reference is historical business data. Customer.delete()
        # would cascade through Order.customer and can silently erase unpaid,
        # cancelled, failed, or otherwise unsettled orders as well.
        has_orders = bool(orders)
        has_order_transactions = CustomerTransaction.objects.filter(
            order__customer=customer,
        ).exists()

        if has_account_history or has_orders or has_order_transactions:
            raise ValidationError(
                "Customers with wallet history or order history cannot be deleted."
            )
        customer.delete()
