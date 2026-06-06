// core/application/use-cases/table/UpdateTable.ts
import { z } from 'zod';
import type { TableRepository } from '../../../repositories/product/TableRepository';

const UpdateTableSchema = z.object({
    number: z.string().min(1).optional(),
    capacity: z.number().int().positive().optional(),
    section: z.string().nullable().optional(),
    isActive: z.boolean().optional(),
    isAvailable: z.boolean().optional(),

});

export type UpdateTableInput = z.infer<typeof UpdateTableSchema>;

export class UpdateTable {
    constructor(private tableRepository: TableRepository) {}

    async execute(id: string, input: UpdateTableInput): Promise<void> {
        if (!id) throw new Error('شناسه میز معتبر نیست');
        const validated = UpdateTableSchema.parse(input);
        await this.tableRepository.update(id, validated);
    }
}