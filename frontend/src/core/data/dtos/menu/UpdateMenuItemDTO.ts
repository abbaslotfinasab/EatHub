// core/application/dto/menu/CreateMenuDTO.ts

export interface UpdateMenuItemDTO {
    id?:string;
    name: string;
    description: string | null;
    price: number;
    image_url: string | null;
}