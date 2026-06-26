// core/domain/repositories/sales/MenuRepository.ts
import type {MenuItem} from "../../entities/product/menu/MenuItem.ts";
import type {MenuResult} from "../../entities/product/menu/MenuResult.ts";
import type {MenuFilters} from "../../objects/filters/MenuFilters.ts";
import type {PublicRestaurantMenu} from "../../entities/product/PublicRestaurantMenu.ts";
import type {MenuFormInput} from "../../objects/forms/MenuFormInput.ts";


export interface MenuRepository {
    // ایجاد منو به همراه آیتم‌هایش (atomic)
    createWithItems(
        input: MenuFormInput
    ): Promise<MenuResult>;

    delete(id: string): Promise<void>;

    findById(id: string): Promise<MenuResult | null>;

    findAll(filters?: MenuFilters): Promise<MenuResult[]>;

    findPublicBySlug(
        slug: string
    ): Promise<PublicRestaurantMenu>;

    findMenuItemById(id: string): Promise<MenuItem | null>;

    update(
        id: string,
        menu: MenuFormInput,
    ): Promise<MenuResult>;

}