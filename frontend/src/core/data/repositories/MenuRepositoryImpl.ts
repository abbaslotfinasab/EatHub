// core/data/repositories/MenuRepositoryImpl.ts

import type {MenuRepository} from "../../domain/repositories/product/MenuRepository";

import type {MenuWithItems} from "../../domain/entities/product/menu/MenuWithItems.ts";
import type {MenuItem} from "../../domain/entities/product/menu/MenuItem";

import {MenuRemoteDataSource} from "../datasources/MenuRemoteDataSource";

import {menuMapper} from "../mappers/menuMapper.ts";

import {publicRestaurantMenuMapper} from "../mappers/publicRestaurantMenuMapper";

import type {PublicRestaurantMenu} from "../../domain/entities/product/PublicRestaurantMenu";

export class MenuRepositoryImpl implements MenuRepository {

    constructor(
        private remote: MenuRemoteDataSource,
    ) {
    }


    // ------------------------
    // Create
    // ------------------------

    async create(
        input: MenuWithItems,
    ): Promise<void> {

        const payload = menuMapper.toCreateDTO(input);

        await this.remote.createMenu(payload);

    }

    // ------------------------
    // Find One
    // ------------------------

    async findById(
        id: number,
    ): Promise<MenuWithItems | null> {

        const dto = await this.remote.getMenuById(id);

        if (!dto) {
            return null;
        }

        return menuMapper.toDomain(dto);
    }

    // ------------------------
    // Find All
    // ------------------------

    async findAll(): Promise<MenuWithItems[]> {

        const dtos = await this.remote.getMenus();

        return dtos.map(menuMapper.toDomain);
    }

    // ------------------------
    // Update
    // ------------------------

    async update(
        input: MenuWithItems,
    ): Promise<void> {

        const payload = menuMapper.toUpdateDTO(input);

        await this.remote.updateMenu(payload.id,payload);


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
        id: number,
    ): Promise<MenuItem | null> {

        const menu = await this.findById(id);

        if (!menu) {
            return null;
        }

        return menu.items.find(i => i.id === id) ?? null;
    }

}