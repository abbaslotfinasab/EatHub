import type { PurchaseOrderItemDTO } from "./PurchaseOrderItemDTO";

export interface PurchaseOrderDTO {
    id: string;

    supplier_id?: string;

    supplier_name: string;

    supplier_number: string;

    type: string;

    status: string;

    subtotal: number;             // جمع قیمت اقلام (بدون تخفیف)

    discount: number | null;             // مبلغ تخفیف

    tax: number | null;                  // مالیات (در صورت وجود)

    total_amount: number;          // مبلغ نهایی = subtotal - discount + tax

    invoice_number: string | null;

    notes: string | null;

    items: PurchaseOrderItemDTO[];

    created_at: string;
    updated_at: string;
}