export interface MenuItemDTO {
    id: string;
    menuId: string;

    name: string;
    description: string | null;

    price: number;
    image_url:string, // مهم

    is_available: boolean;

    created_at: string;
    updated_at: string;
}