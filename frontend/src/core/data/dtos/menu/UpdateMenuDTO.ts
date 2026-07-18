import type {CreateMenuItemDTO} from "./CreateMenuItemDTO.ts";

export interface UpdateMenuDTO {
    id:string;
    name: string;
    category: string;
    description: string | null;
    sort_order: number;

    items: CreateMenuItemDTO[];
}