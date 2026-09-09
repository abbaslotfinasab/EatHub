from django.db.models import Q

from purchase.domain.entities.supplier import Supplier
from purchase.domain.repositories.supplier_repository import (
    SupplierRepository,
)
from purchase.infrastructure.persistence.django.mappers import SupplierMapper
from purchase.models import Supplier as DjangoSupplier


class DjangoSupplierRepository(SupplierRepository):
    def get_by_id_for_business(
        self,
        supplier_id: int,
        business_id: int,
    ) -> Supplier | None:
        model = DjangoSupplier.objects.filter(
            id=supplier_id,
            business_id=business_id,
        ).first()

        if model is None:
            return None

        return SupplierMapper.to_domain(model)

    def get_by_name(
        self,
        business_id: int,
        name: str,
    ) -> Supplier | None:
        model = DjangoSupplier.objects.filter(
            business_id=business_id,
            name=name,
        ).first()

        if model is None:
            return None

        return SupplierMapper.to_domain(model)

    def list(
        self,
        business_id: int,
        *,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> list[Supplier]:
        queryset = DjangoSupplier.objects.filter(
            business_id=business_id,
        )

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(phone__icontains=search)
                | Q(email__icontains=search)
                | Q(tax_number__icontains=search)
            )

        return [
            SupplierMapper.to_domain(model)
            for model in queryset.order_by("id")
        ]

    def exists_by_name(
        self,
        business_id: int,
        name: str,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        queryset = DjangoSupplier.objects.filter(
            business_id=business_id,
            name=name,
        )

        if exclude_id is not None:
            queryset = queryset.exclude(id=exclude_id)

        return queryset.exists()

    def save(
        self,
        supplier: Supplier,
    ) -> Supplier:
        if supplier.id is None:
            model = SupplierMapper.to_model(supplier)
        else:
            model = DjangoSupplier.objects.filter(
                id=supplier.id,
                business_id=supplier.business_id,
            ).first()

            if model is None:
                raise ValueError(
                    "Supplier does not exist in the specified business."
                )

            if model.business_id != supplier.business_id:
                raise ValueError("Supplier business cannot be changed.")

            model = SupplierMapper.to_model(supplier, model)

        model.save()

        return SupplierMapper.to_domain(model)
