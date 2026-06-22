import type {MenuRepository} from "../../../repositories/product/MenuRepository.ts";

export class GetPublicMenus {
    constructor(
        private menuRepository: MenuRepository
    ) {}

    async execute(slug: string) {
        return this.menuRepository.findPublicBySlug(
            slug
        );
    }
}