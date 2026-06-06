// core/application/use-cases/table/GetTableById.ts
import type { TableRepository } from '../../../repositories/product/TableRepository';

export class GetTableById {
    constructor(private tableRepository: TableRepository) {}

    async execute(id: string) {
        if (!id) throw new Error('شناسه میز معتبر نیست');
        return this.tableRepository.findById(id);
    }
}