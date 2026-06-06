// core/application/use-cases/table/CheckTableAvailability.ts
import { z } from 'zod';
import type { TableRepository } from '../../../repositories/product/TableRepository';

const CheckAvailabilitySchema = z.object({
    tableId: z.string(),
    date: z.string().date(),
    startTime: z.string().regex(/^([01]\d|2[0-3]):([0-5]\d)$/),
    endTime: z.string().regex(/^([01]\d|2[0-3]):([0-5]\d)$/),
    excludeReservationId: z.string().optional(),
});

export class CheckTableAvailability {
    constructor(private tableRepository: TableRepository) {}

    async execute(input: z.infer<typeof CheckAvailabilitySchema>): Promise<boolean> {
        const { tableId, date, startTime, endTime, excludeReservationId } = CheckAvailabilitySchema.parse(input);
        return this.tableRepository.isTableAvailable(tableId, date, startTime, endTime, excludeReservationId);
    }
}