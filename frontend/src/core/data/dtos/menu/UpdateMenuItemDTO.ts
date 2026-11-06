// core/application/dto/menu/CreateMenuDTO.ts

export interface UpdateMenuItemDTO {
    id?:number;
    name: string;
    recipe_id: number | null;
    description: string | null;
    price: number;
    image_url: string | null;
}