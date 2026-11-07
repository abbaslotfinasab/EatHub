import type {MenuItem} from "../../entities/product/menu/MenuItem.ts";
import type {MenuWithItems} from "../../entities/product/menu/MenuWithItems.ts";
import type {MenuFilters} from "../../objects/filters/MenuFilters.ts";
import type {PublicRestaurantMenu} from "../../entities/product/PublicRestaurantMenu.ts";
import type {MenuFilters} from "../../objects/filters/MenuFilters.ts";

export interface MenuRepository {
    create(input: MenuWithItems): Promise<void>;
    delete(id: string): Promise<void>;
    findById(id: number): Promise<MenuWithItems | null>;
    findAll(filters?: MenuFilters): Promise<MenuWithItems[]>;
    findPublicBySlug(slug: string): Promise<PublicRestaurantMenu>;
    findMenuItemById(id: number): Promise<MenuItem | null>;
    update(menu: MenuWithItems): Promise<void>;
    updateMenuItem(id: number, input: Partial<MenuItem>): Promise<MenuItem>;
    deleteMenuItem(id: number): Promise<void>;
}
