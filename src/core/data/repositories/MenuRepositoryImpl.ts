// core/data/repositories/MenuRepositoryImpl.ts
import { apiClient } from '../http/http-client';
import { isAxiosError } from 'axios';
import type {MenuRepository} from "../../domain/repositories/product/MenuRepository.ts";
import type {Menu} from "../../domain/entities/product/Menu.ts";
import type {MenuItem} from "../../domain/entities/product/MenuItem.ts";
import type {MenuResult} from "../../domain/entities/product/MenuResult.ts";
import type {MenuFilters} from "../../domain/objects/filters/MenuFilters.ts";

export class MenuRepositoryImpl implements MenuRepository {

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
    // ایجاد منو به همراه آیتم‌های منو (یک درخواست)
    async createWithItems(
        menu: Omit<Menu, 'id' | 'createdAt' | 'updatedAt'>,
        items: Omit<MenuItem, 'id' | 'createdAt' | 'updatedAt' | 'menuId'>[]
    ): Promise<MenuResult> {
        const response = await apiClient.post('/menus/with-items', { menu, items });
        return response.data;
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
    async findAll(filters?: MenuFilters): Promise<MenuResult[]> {
        const params = new URLSearchParams();
        if (filters) {
            Object.entries(filters).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                    params.append(key, String(value));
                }
            });
        }
        const queryString = params.toString();
        const url = queryString ? `/menus?${queryString}` : '/menus';
        const response = await apiClient.get(url);
        return response.data;
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