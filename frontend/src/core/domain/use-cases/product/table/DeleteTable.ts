// core/application/use-cases/table/DeleteTable.ts
import type { TableRepository } from '../../../repositories/product/TableRepository';

export class DeleteTable {
    constructor(private tableRepository: TableRepository) {}

    async execute(id: string): Promise<void> {
        if (!id) throw new Error('شناسه میز معتبر نیست');
        await this.tableRepository.delete(id);
    }
}