// core/data/repositories/MaterialRepositoryImpl.ts
import type {MaterialRepository} from '../../domain/repositories/inventory/MaterialRepository';
import type {Material} from '../../domain/entities/inventory/Material';
import type {MaterialIngredient} from '../../domain/entities/inventory/MaterialIngredient';
import {apiClient} from '../http/http-client';
import {isAxiosError} from 'axios';
import type {MaterialResult} from "../../domain/entities/inventory/MaterialResult.ts";
import type {MaterialFilters} from "../../domain/objects/filters/MaterialFilters.ts";
import {mockMaterials} from "../dtos/material/material.ts";


const getMockIngredientsForMaterial = (materialId: string): MaterialIngredient[] => {
    if (materialId === 'mat-1') {
        return [
            {
                id: 'ing-1',
                materialId: 'mat-1',
                ingredientId: 'ingredient-1',
                quantity: 2,
                unitId:'3edsf',
            },
            // ...
        ];
    }
    return [];
};
export class MaterialRepositoryImpl implements MaterialRepository {
    // ایجاد ماده مرکب به همراه مواد مصرفی (یک درخواست)
    async createWithIngredients(
        materialData: Omit<Material, 'id' | 'createdAt' | 'updatedAt'>,
        ingredientsData: Omit<MaterialIngredient, 'id' | 'createdAt' | 'updatedAt' | 'materialId'>[]
    ): Promise<MaterialResult> {
        const response = await apiClient.post('/materials/with-ingredients', {
            material: materialData,
            ingredients: ingredientsData,
        });
        return response.data;
    }

    // پیدا کردن ماده مرکب با شناسه (بدون مواد مصرفی)
    async findById(id: string): Promise<MaterialResult | null> {
        try {
            const response = await apiClient.get(`/materials/${id}`);
            return response.data;
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }

    // پیدا کردن ماده مرکب به همراه مواد مصرفی
    async findWithIngredientsById(id: string): Promise<MaterialResult | null> {
        try {
            const response = await apiClient.get(`/materials/${id}/with-ingredients`);
            return response.data;
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }


    // دریافت تمام مواد مرکب (بدون مواد مصرفی) با قابلیت فیلتر
    async findAll(filters?: MaterialFilters): Promise<MaterialResult[]> {
        // اگر از API واقعی استفاده می‌کنید، این بخش را فعال کنید
        // const params = new URLSearchParams();
        // if (filters) {
        //     Object.entries(filters).forEach(([key, value]) => {
        //         if (value !== undefined && value !== null) {
        //             params.append(key, String(value));
        //         }
        //     });
        // }
        // const queryString = params.toString();
        // const url = queryString ? `/materials?${queryString}` : '/materials';
        // const response = await apiClient.get(url);
        // return response.data; // فرض می‌کنیم پاسخ API آرایه‌ای از MaterialResult است

        // ---------- حالت mock (برای تست طراحی) ----------
        let filteredMaterials = [...mockMaterials];

        // اعمال فیلترها روی mockMaterials
        if (filters?.search) {
            const term = filters.search.toLowerCase();
            filteredMaterials = filteredMaterials.filter(m => m.name.toLowerCase().includes(term));
        }
        if (filters?.lowStock) {
            filteredMaterials = filteredMaterials.filter(m => m.currentStock <= m.reorderLevel);
        }

        // تبدیل هر Material به MaterialResult (با ingredients خالی یا mock)
        return filteredMaterials.map(material => ({
            material,
            ingredients: getMockIngredientsForMaterial(material.id!), // در صورت نیاز مواد مصرفی mock شده
        }));
    }

    // به‌روزرسانی ماده مرکب و جایگزینی کامل مواد مصرفی
    async updateWithIngredients(
        materialId: string,
        materialData: Partial<Omit<Material, 'id' | 'createdAt' | 'updatedAt'>>,
        ingredients?: Omit<MaterialIngredient, 'id' | 'createdAt' | 'updatedAt' | 'materialId'>[]
    ): Promise<MaterialResult> {
        const response = await apiClient.put(`/materials/${materialId}/with-ingredients`, {
            materialData,
            ingredients,
        });
        return response.data;
    }

    // به‌روزرسانی فقط ماده مرکب (بدون مواد مصرفی)
    async update(id: string, data: Partial<Material>): Promise<MaterialResult> {
        const response = await apiClient.patch(`/materials/${id}`, data);
        return response.data;
    }

    // حذف ماده مرکب به همراه تمام مواد مصرفی (cascade)
    async deleteWithIngredients(materialId: string): Promise<void> {
        await apiClient.delete(`/materials/${materialId}/with-ingredients`);
    }

    // حذف فقط ماده مرکب (در صورت عدم وابستگی)
    async delete(id: string): Promise<void> {
        await apiClient.delete(`/materials/${id}`);
    }

    // به‌روزرسانی موجودی (اختیاری)
    async updateStock(id: string, newStock: number): Promise<void> {
        await apiClient.patch(`/materials/${id}/stock`, { currentStock: newStock });
    }

    async creat(materialData: Omit<Material, "id" | "createdAt" | "updatedAt">, ingredientsData: Omit<MaterialIngredient, "id" | "createdAt" | "updatedAt" | "materialId">[]): Promise<MaterialResult> {
        const response = await apiClient.post('/materials', {
            materialData:materialData,
            ingredientsData:ingredientsData

        });
        return response.data;
    }

}