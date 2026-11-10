export interface MenuAllergenDTO {
    code: string;
    presence: "contains" | "may_contain";
}

export interface MenuItemDTO {
    id: number;
    menuId?: string;
    name: string;
    recipe_id?: number | null;
    recipe_name?: string | null;
    product_id?: number | null;
    product_name?: string | null;
    recipe_allergens?: MenuAllergenDTO[] | null;
    catalog_product_allergens?: MenuAllergenDTO[] | null;
    description: string | null;
    price: number;
    image_url: string | null;
    is_available: boolean;
    created_at?: string;
    updated_at?: string;
}