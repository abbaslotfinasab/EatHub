export type ProductStatus = "draft" | "active" | "archived";

export interface Product {
    id: number;
    name: string;
    sku: string | null;
    category: string | null;
    description: string | null;
    imageUrl: string | null;
    status: ProductStatus;
    createdAt: string;
    updatedAt: string;
}

export interface ProductInput {
    name: string;
    sku?: string | null;
    category?: string | null;
    description?: string | null;
    imageUrl?: string | null;
    status?: ProductStatus;
}

export interface ProductPage {
    count: number;
    page: number;
    pageSize: number;
    results: Product[];
}
