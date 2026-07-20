import type {CreateMenuItemDTO} from "./CreateMenuItemDTO.ts";

export interface UpdateMenuDTO {
    id:number;
    name: string;
    category: string;
    description: string | null;
    sort_order: number;

    items: CreateMenuItemDTO[];
}