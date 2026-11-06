export interface MenuItemDTO {
    id: number;
    menuId?: string;
    name: string;
    description: string | null;
    price: number;
    image_url: string | null;
    is_available: boolean;
    created_at?: string;
    updated_at?: string;
}
