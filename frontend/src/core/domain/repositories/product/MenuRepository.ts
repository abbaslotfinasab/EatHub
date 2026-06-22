// core/domain/repositories/sales/MenuRepository.ts
import type { Menu } from '../../entities/product/Menu';
import type {MenuItem} from "../../entities/product/MenuItem.ts";
import type {MenuResult} from "../../entities/product/MenuResult.ts";
import type {MenuFilters} from "../../objects/filters/MenuFilters.ts";
import type {PublicRestaurantMenu} from "../../entities/product/PublicRestaurantMenu.ts";



export interface MenuRepository {
    // ایجاد منو به همراه آیتم‌هایش (atomic)
    createWithItems(
        menu: Omit<Menu, 'id' | 'createdAt' | 'updatedAt'>,
        items: Omit<MenuItem, 'id' | 'createdAt' | 'updatedAt' | 'menuId' | 'imageUrl'>[]
    ): Promise<MenuResult>;
    delete(id: string): Promise<void>;
    findById(id: string): Promise<MenuResult | null>;
    findAll(filters?: MenuFilters): Promise<MenuResult[]>;
     findPublicBySlug(
        slug: string
    ): Promise<PublicRestaurantMenu>;
    findMenuItemById(id: string): Promise<MenuItem | null>;
    update(
        menuId: string,
        menuData: Partial<Omit<Menu, 'id' | 'createdAt' | 'updatedAt'>>,
        items?: Omit<MenuItem, 'createdAt' | 'updatedAt' | 'menuId'>[] // در صورت ارسال، جایگزین کامل (id اختیاری برای آپدیت)
    ): Promise<MenuResult>;}