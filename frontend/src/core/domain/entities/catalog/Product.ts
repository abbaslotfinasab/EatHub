export type ProductStatus = "draft" | "active" | "archived";
export type ProductAllergenCode =
    | "celery" | "cereals_gluten" | "crustaceans" | "eggs" | "fish" | "lupin"
    | "milk" | "molluscs" | "mustard" | "peanuts" | "sesame" | "soybeans"
    | "sulphites" | "tree_nuts";
export type ProductAllergenPresence = "contains" | "may_contain";
export type ProductDietaryTagCode =
    | "vegan" | "vegetarian" | "gluten_free" | "dairy_free" | "halal" | "kosher";

export interface ProductAllergenDeclaration {
    code: ProductAllergenCode;
    presence: ProductAllergenPresence;
}

export interface Product {
    id: number;
    name: string;
    sku: string | null;
    category: string | null;
    description: string | null;
    imageUrl: string | null;
    status: ProductStatus;
    allergens: ProductAllergenDeclaration[];
    dietaryTags: ProductDietaryTagCode[];
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
    allergens?: ProductAllergenDeclaration[];
    dietaryTags?: ProductDietaryTagCode[];
}

export interface ProductPage {
    count: number;
    page: number;
    pageSize: number;
    results: Product[];
}
