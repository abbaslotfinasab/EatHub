from django.db import transaction

from products.models import Customer, CustomerAccount


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
        customer.delete()

    @staticmethod
    @staticmethod
    @transaction.atomic
    def get_or_create_customer(*, business, name, phone):

        if not phone:
            return None

        customer, created = Customer.objects.get_or_create(
            business=business,
            phone=phone,
            defaults={
                "name": name or "Guest",
            },
        )

        if not created and name and customer.name != name:
            customer.name = name
            customer.save(update_fields=["name"])

        return customer