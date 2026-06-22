// core/application/dto/menu/CreateMenuDTO.ts

export interface CreateMenuItemDTO {
    name: string;
    description?: string | null;
    price: number;
    image_url?: string | null;
}