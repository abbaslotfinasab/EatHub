export interface ProductDTO {
    id: number;
    name: string;
    sku: string | null;
    category: string | null;
    description: string | null;
    image_url: string | null;
    status: "draft" | "active" | "archived";
    created_at: string;
    updated_at: string;
}

export interface ProductPageDTO {
    count: number;
    page: number;
    page_size: number;
    results: ProductDTO[];
}

export interface ProductInputDTO {
    name?: string;
    sku?: string | null;
    category?: string | null;
    description?: string | null;
    image_url?: string | null;
    status?: "draft" | "active" | "archived";
}
