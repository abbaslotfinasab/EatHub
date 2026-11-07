import type {MenuRepository} from "../../domain/repositories/product/MenuRepository";
import type {MenuWithItems} from "../../domain/entities/product/menu/MenuWithItems.ts";
import type {MenuItem} from "../../domain/entities/product/menu/MenuItem";
import {MenuRemoteDataSource} from "../datasources/MenuRemoteDataSource";
import {menuMapper} from "../mappers/menuMapper.ts";
import {publicRestaurantMenuMapper} from "../mappers/publicRestaurantMenuMapper";
import type {PublicRestaurantMenu} from "../../domain/entities/product/PublicRestaurantMenu";
import type {UpdateMenuItemDTO} from "../dtos/menu/UpdateMenuItemDTO.ts";

export class MenuRepositoryImpl implements MenuRepository {
    constructor(private remote: MenuRemoteDataSource) {}

    async create(input: MenuWithItems): Promise<void> {
        await this.remote.createMenu(menuMapper.toCreateDTO(input));
    }

    async findById(id: number): Promise<MenuWithItems | null> {
        const dto = await this.remote.getMenuById(id);
        return dto ? menuMapper.toDomain(dto) : null;
    }

    async findAll(): Promise<MenuWithItems[]> {
        const dtos = await this.remote.getMenus();
        return dtos.map(menuMapper.toDomain);
    }

    async update(input: MenuWithItems): Promise<void> {
        const payload = menuMapper.toUpdateDTO(input);
        await this.remote.updateMenu(payload.id, payload);
    }

    async delete(id: string): Promise<void> {
        await this.remote.deleteMenu(id);
    }

    async findPublicBySlug(slug: string): Promise<PublicRestaurantMenu> {
        const dto = await this.remote.getPublicMenus(slug);
        return publicRestaurantMenuMapper.toDomain(dto);
    }

    async findMenuItemById(id: number): Promise<MenuItem | null> {
        const menus = await this.findAll();
        for (const menu of menus) {
            const item = menu.items.find((candidate) => candidate.id === id);
            if (item) return item;
        }
        return null;
    }

    async updateMenuItem(id: number, input: Partial<MenuItem>): Promise<MenuItem> {
        const payload: UpdateMenuItemDTO = {
            ...(input.name !== undefined ? {name: input.name} : {}),
            ...(input.recipeId !== undefined ? {recipe_id: input.recipeId == null || input.recipeId === "" ? null : Number(input.recipeId)} : {}),
            ...(input.description !== undefined ? {description: input.description} : {}),
            ...(input.price !== undefined ? {price: input.price} : {}),
            ...(input.imageUrl !== undefined ? {image_url: input.imageUrl} : {}),
            ...(input.isAvailable !== undefined && input.isAvailable !== null ? {is_available: input.isAvailable} : {}),
        };
        const dto = await this.remote.updateMenuItem(id, payload);
        return menuMapper.toMenuItem(dto);
    }

    async deleteMenuItem(id: number): Promise<void> {
        await this.remote.deleteMenuItem(id);
    }
}
