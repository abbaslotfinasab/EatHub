export interface MenuItemDTO {
    id: string;

    name: string;
    description: string | null;

    price: number;
    image_url:string, // مهم

    is_available: boolean;
    recipe_id: string;

    created_at: string;
    updated_at: string;
}