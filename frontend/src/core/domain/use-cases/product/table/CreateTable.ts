// core/application/use-cases/table/CreateTable.ts
import { z } from 'zod';
import type { TableRepository } from '../../../repositories/product/TableRepository';

const CreateTableSchema = z.object({
    number: z.string().min(1, 'شماره میز الزامی است'),
    capacity: z.number().int().positive('ظرفیت باید عدد مثبت باشد'),
    section: z.string().nullable().optional(),
    isActive: z.boolean().default(true),
});

export type CreateTableInput = z.infer<typeof CreateTableSchema>;

export class CreateTable {
    constructor(private tableRepository: TableRepository) {}

    async execute(input: CreateTableInput): Promise<void> {
        const validated = CreateTableSchema.parse(input);
        await this.tableRepository.save(validated);
    }
}