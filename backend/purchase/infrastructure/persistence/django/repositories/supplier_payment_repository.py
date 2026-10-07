from datetime import date

from purchase.domain.entities.supplier_payment import SupplierPayment
from purchase.domain.enums.payment_method import PaymentMethod
from purchase.domain.repositories.supplier_payment_repository import (
    SupplierPaymentRepository,
)
from purchase.infrastructure.persistence.django.mappers import SupplierPaymentMapper
from purchase.models import (
    Supplier as DjangoSupplier,
    SupplierPayment as DjangoSupplierPayment,
)


class DjangoSupplierPaymentRepository(SupplierPaymentRepository):
    def lock_for_allocation(self, business_id: int, supplier_payment_id: int) -> bool:
        return DjangoSupplierPayment.objects.select_for_update(of=("self",)).filter(
            id=supplier_payment_id,
            business_id=business_id,
        ).exists()

    def get_by_id_for_business(
        self,
        supplier_payment_id: int,
        business_id: int,
    ) -> SupplierPayment | None:
        model = DjangoSupplierPayment.objects.filter(
            id=supplier_payment_id,
            business_id=business_id,
        ).first()
        return None if model is None else SupplierPaymentMapper.to_domain(model)

    def list(
        self,
        business_id: int,
        *,
        supplier_id: int | None = None,
        invoice_id: int | None = None,
        method: PaymentMethod | None = None,
        payment_date_from: date | None = None,
        payment_date_to: date | None = None,
    ) -> list[SupplierPayment]:
        queryset = DjangoSupplierPayment.objects.filter(business_id=business_id)
        if supplier_id is not None:
            queryset = queryset.filter(supplier_id=supplier_id)
        if invoice_id is not None:
            queryset = queryset.filter(invoice_id=invoice_id)
        if method is not None:
            queryset = queryset.filter(method=method.value)
        if payment_date_from is not None:
            queryset = queryset.filter(payment_date__gte=payment_date_from)
        if payment_date_to is not None:
            queryset = queryset.filter(payment_date__lte=payment_date_to)
        return [
            SupplierPaymentMapper.to_domain(model)
            for model in queryset.order_by("id")
        ]

    def save(self, supplier_payment: SupplierPayment) -> SupplierPayment:
        supplier_payment.validate()
        if not DjangoSupplier.objects.filter(
            id=supplier_payment.supplier_id,
            business_id=supplier_payment.business_id,
        ).exists():
            raise ValueError("Supplier does not exist in this business.")
        if supplier_payment.id is None:
            model = SupplierPaymentMapper.to_model(supplier_payment)
        else:
            model = DjangoSupplierPayment.objects.filter(
                id=supplier_payment.id,
                business_id=supplier_payment.business_id,
            ).first()
            if model is None:
                raise ValueError(
                    "Supplier payment does not exist in the specified business."
                )
            model = SupplierPaymentMapper.to_model(supplier_payment, model)
        model.save()
        return SupplierPaymentMapper.to_domain(model)
