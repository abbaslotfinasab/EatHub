import type {MenuRepository} from "../../../repositories/product/MenuRepository.ts";

export class DeleteMenuItem {
    constructor(private repository: MenuRepository) {}

    execute(id: number): Promise<void> {
        return this.repository.deleteMenuItem(id);
    }
}
