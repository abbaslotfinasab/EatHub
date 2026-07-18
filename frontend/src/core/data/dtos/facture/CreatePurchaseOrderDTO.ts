import type {CreatePurchaseOrderItemDTO} from "./CreatePurchaseOrderItemDTO.ts";

export interface CreatePurchaseOrderDTO {
    supplier_id?: string;

    supplier_name: string | null;

    supplier_number: string | null;

    status: string;

    subtotal: number | null;             // جمع قیمت اقلام (بدون تخفیف)

    discount: number | null;             // مبلغ تخفیف

    tax: number | null;                  // مالیات (در صورت وجود)

    total_amount: number | null;          // مبلغ نهایی = subtotal - discount + tax

    invoice_number: string | null;

    notes: string | null;

    items: CreatePurchaseOrderItemDTO[];

}