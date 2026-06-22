import type {CreateMenuItemDTO} from "./CreateMenuItemDTO.ts";

export interface CreateMenuDTO {
    name: string;
    category: string;
    description?: string | null;
    sort_order: number;

    items: CreateMenuItemDTO[];
}