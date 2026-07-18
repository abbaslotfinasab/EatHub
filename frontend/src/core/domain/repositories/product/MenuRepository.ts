// core/domain/repositories/sales/MenuRepository.ts
import type {MenuItem} from "../../entities/product/menu/MenuItem.ts";
import type {MenuWithItems} from "../../entities/product/menu/MenuWithItems.ts";
import type {MenuFilters} from "../../objects/filters/MenuFilters.ts";
import type {PublicRestaurantMenu} from "../../entities/product/PublicRestaurantMenu.ts";


export interface MenuRepository {
    // ایجاد منو به همراه آیتم‌هایش (atomic)
    create(
        input: MenuWithItems
    ): Promise<void>;

    delete(id: string): Promise<void>;

    findById(id: string): Promise<MenuWithItems | null>;

    findAll(filters?: MenuFilters): Promise<MenuWithItems[]>;

    findPublicBySlug(
        slug: string
    ): Promise<PublicRestaurantMenu>;

    findMenuItemById(id: string): Promise<MenuItem | null>;

    update(
        menu: MenuWithItems,
    ): Promise<void>;

}