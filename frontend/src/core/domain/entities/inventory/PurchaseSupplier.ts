export interface PurchaseSupplier {
    id: string;
    businessId: string;
    name: string;
    phone: string;
    email: string;
    address: string;
    taxNumber: string;
    notes: string;
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
}

export interface PurchaseSupplierInput {
    name: string;
    phone: string;
    email: string;
    address: string;
    taxNumber: string;
    notes: string;
    isActive: boolean;
}
