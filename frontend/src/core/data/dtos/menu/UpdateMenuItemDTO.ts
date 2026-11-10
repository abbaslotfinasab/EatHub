export interface UpdateMenuItemDTO {
    name?: string;
    recipe_id?: number | null;
    product_id?: number | null;
    description?: string | null;
    price?: number;
    image_url?: string | null;
    is_available?: boolean;
}