import type {
    ProductAllergenDeclaration,
    ProductDietaryTagCode,
    ProductStatus,
} from "../../../domain/entities/catalog/Product.ts";

export interface ProductDTO {
    id: number;
    name: string;
    sku: string | null;
    category: string | null;
    description: string | null;
    image_url: string | null;
    status: ProductStatus;
    allergens: ProductAllergenDeclaration[];
    dietary_tags: ProductDietaryTagCode[];
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
    status?: ProductStatus;
    allergens?: ProductAllergenDeclaration[];
    dietary_tags?: ProductDietaryTagCode[];
}
