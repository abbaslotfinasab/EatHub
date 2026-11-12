export interface PurchaseSupplierDTO {
    id: number;
    business_id: number;
    name: string;
    phone: string;
    email: string;
    address: string;
    tax_number: string;
    notes: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface PurchaseSupplierWriteDTO {
    name: string;
    phone: string;
    email: string;
    address: string;
    tax_number: string;
    notes: string;
    is_active?: boolean;
}
