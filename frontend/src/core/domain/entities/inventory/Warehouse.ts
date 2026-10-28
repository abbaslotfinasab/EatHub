export interface Warehouse {
    id: string;
    name: string;
    code: string | null;
    isActive: boolean;
    isDefault: boolean;
    createdAt: string;
    updatedAt: string;
}

export interface WarehouseInput {
    name: string;
    code?: string | null;
    isActive?: boolean;
    isDefault?: boolean;
}

export interface WarehousePage {
    count: number;
    page: number;
    pageSize: number;
    results: Warehouse[];
}
