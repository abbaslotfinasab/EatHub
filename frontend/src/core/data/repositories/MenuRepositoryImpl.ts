// core/data/repositories/MenuRepositoryImpl.ts
import {apiClient} from '../http/http-client';
import {isAxiosError} from 'axios';
import type {MenuRepository} from "../../domain/repositories/product/MenuRepository.ts";
import type {Menu} from "../../domain/entities/product/Menu.ts";
import type {MenuItem} from "../../domain/entities/product/MenuItem.ts";
import type {MenuResult} from "../../domain/entities/product/MenuResult.ts";
import {MenuRemoteDataSource} from "../datasources/MenuRemoteDataSource.ts";
import {menuMapper} from "../mappers/menu.mapper.ts";
import {publicRestaurantMenuMapper} from "../mappers/publicRestaurantMenuMapper.ts";
import type {PublicRestaurantMenu} from "../../domain/entities/product/PublicRestaurantMenu.ts";

export class MenuRepositoryImpl implements MenuRepository {
    constructor(
        private remote: MenuRemoteDataSource
    ) {
    }

    async uploadImage(file: File): Promise<string> {
        const result = await this.remote.uploadImage(file);
        return result.url;
    }

    async findMenuItemById(id: string): Promise<MenuItem | null> {
        try {
            const response = await apiClient.get(`/menus/${id}`);
            return response.data;
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }

    async createWithItems(
        menu: Omit<Menu, 'id' | 'createdAt' | 'updatedAt'>,
        items: Omit<MenuItem, 'id' | 'createdAt' | 'updatedAt' | 'menuId'>[]
    ): Promise<MenuResult> {

        const mappedItems = await Promise.all(
            items.map(async (item) => {

                let imageUrl: string | null = null;

                if (item.imageFile) {
                    imageUrl = await this.uploadImage(
                        item.imageFile
                    );

                    console.log("UPLOADED URL =>", imageUrl);

                }

                return {
                    name: item.name,
                    description: item.description,
                    price: item.price,
                    image_url: imageUrl,
                };
            })
        );

        return await this.remote.createMenu({
            name: menu.name,
            category: menu.category,
            description: menu.description,
            sort_order: menu.sortOrder,

            items: mappedItems,
        });
    }


    // پیدا کردن یک منو با شناسه (بدون آیتم‌ها)
    async findById(id: string): Promise<MenuResult | null> {
        try {
            const response = await apiClient.get(`/menus/${id}`);
            return response.data;
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }

    // دریافت لیست منوها با قابلیت فیلتر
    async findAll() {

        const menus = await this.remote.getMenus();

        console.log("API RESPONSE =>", menus);

        return menus.map(menuMapper.toDomain);
    }

    async findPublicBySlug(
        slug: string
    ): Promise<PublicRestaurantMenu> {

        const dto =
            await this.remote.getPublicMenus(slug);

        return publicRestaurantMenuMapper.toDomain(dto);


    }

    // به‌روزرسانی جزئی منو
    async update(id: string, data: Partial<Menu>): Promise<MenuResult> {
        const response = await apiClient.patch(`/menus/${id}`, data);
        return response.data;
    }

    // حذف منو (فقط منو – آیتم‌ها در بک‌اند با CASCADE حذف می‌شوند)
    async delete(id: string): Promise<void> {
        await apiClient.delete(`/menus/${id}`);
    }
}