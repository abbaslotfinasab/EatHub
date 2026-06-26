// core/data/repositories/MenuRepositoryImpl.ts

import type {MenuRepository} from "../../domain/repositories/product/MenuRepository";

import type {MenuResult} from "../../domain/entities/product/menu/MenuResult";
import type {MenuItem} from "../../domain/entities/product/menu/MenuItem";

import type {MenuFormInput} from "../../domain/objects/forms/MenuFormInput";

import {MenuRemoteDataSource} from "../datasources/MenuRemoteDataSource";

import {menuMapper} from "../mappers/menu.mapper";

import {publicRestaurantMenuMapper} from "../mappers/publicRestaurantMenuMapper";

import type {PublicRestaurantMenu} from "../../domain/entities/product/PublicRestaurantMenu";

export class MenuRepositoryImpl implements MenuRepository {

    constructor(
        private remote: MenuRemoteDataSource,
    ) {
    }

    // ------------------------
    // Images
    // ------------------------

    private async uploadImage(file: File): Promise<string> {
        const result = await this.remote.uploadImage(file);
        return result.url;
    }

    // ------------------------
    // Create
    // ------------------------

    async createWithItems(
        input: MenuFormInput,
    ): Promise<MenuResult> {

        const items = await Promise.all(
            input.items.map(async (item) => {

                let imageUrl = item.imageUrl;

                if (item.imageFile) {
                    imageUrl = await this.uploadImage(item.imageFile);
                }

                return {
                    name: item.name,
                    description: item.description,
                    price: item.price,
                    image_url: imageUrl,
                    is_available: item.isAvailable,
                };
            }),
        );

        const dto = await this.remote.createMenu({
            name: input.name,
            category: input.category,
            description: input.description,
            sort_order: input.sortOrder,
            items,
        });

        return menuMapper.toDomain(dto);
    }

    // ------------------------
    // Find One
    // ------------------------

    async findById(
        id: string,
    ): Promise<MenuResult | null> {

        const dto = await this.remote.getMenuById(id);

        if (!dto) {
            return null;
        }

        return menuMapper.toDomain(dto);
    }

    // ------------------------
    // Find All
    // ------------------------

    async findAll(): Promise<MenuResult[]> {

        const dtos = await this.remote.getMenus();

        return dtos.map(menuMapper.toDomain);
    }

    // ------------------------
    // Update
    // ------------------------

    async update(
        id: string,
        input: MenuFormInput,
    ): Promise<MenuResult> {

        const items = await Promise.all(
            input.items.map(async (item) => {

                let imageUrl = item.imageUrl;

                if (item.imageFile) {
                    imageUrl = await this.uploadImage(item.imageFile);
                }

                return {
                    ...(item.id ? {id: item.id} : {}),
                    name: item.name,
                    description: item.description,
                    price: item.price,
                    image_url: imageUrl,
                    is_active: item.isAvailable,
                };
            }),
        );

        const dto = await this.remote.updateMenu(id, {
            name: input.name,
            category: input.category,
            description: input.description,
            sort_order: input.sortOrder,
            items,
        });

        return menuMapper.toDomain(dto);
    }

    // ------------------------
    // Delete
    // ------------------------

    async delete(
        id: string,
    ): Promise<void> {

        await this.remote.deleteMenu(id);
    }

    // ------------------------
    // Public
    // ------------------------

    async findPublicBySlug(
        slug: string,
    ): Promise<PublicRestaurantMenu> {

        const dto = await this.remote.getPublicMenus(slug);

        return publicRestaurantMenuMapper.toDomain(dto);
    }

    // ------------------------
    // Menu Item
    // ------------------------

    async findMenuItemById(
        id: string,
    ): Promise<MenuItem | null> {

        const menu = await this.findById(id);

        if (!menu) {
            return null;
        }

        return menu.items.find(i => i.id === id) ?? null;
    }

}