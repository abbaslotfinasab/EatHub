import type {MenuItem} from "../../../entities/product/menu/MenuItem.ts";
import type {MenuRepository} from "../../../repositories/product/MenuRepository.ts";

export class UpdateMenuItem {
    constructor(private repository: MenuRepository) {}

    execute(id: number, input: Partial<MenuItem>): Promise<MenuItem> {
        return this.repository.updateMenuItem(id, input);
    }
}
