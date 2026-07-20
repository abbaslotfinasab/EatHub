import type {MenuItemDTO} from "./MenuItemDTO.ts";

export interface MenuDTO {
    id: number;

    name: string;
    category: string;
    description: string | null;

    sort_order: number;
    is_active: boolean;

    items: MenuItemDTO[];

    created_at: string;
    updated_at: string;
}