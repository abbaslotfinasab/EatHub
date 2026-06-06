// core/application/use-cases/reservation/CreateReservation.ts
import { z } from 'zod';
import type { ReservationRepository } from '../../../repositories/product/ReservationRepository';


const CreateReservationSchema = z.object({
    customerName: z.string().min(2),
    customerPhone: z.string().min(5),
    customerEmail: z.string().email().nullable().optional(),
    tableId: z.string(),
    reservationDate: z.string().date(), // YYYY-MM-DD
    reservationTime: z.string().regex(/^([01]\d|2[0-3]):([0-5]\d)$/),
    partySize: z.number().int().positive(),
    specialRequests: z.string().nullable().optional(),
});

export type CreateReservationInput = z.infer<typeof CreateReservationSchema>;

export class CreateReservation {
    constructor(
        private reservationRepo: ReservationRepository,
    ) {}

    async execute(input: CreateReservationInput) {
        const validated = CreateReservationSchema.parse(input);

        await this.reservationRepo.save(validated);
    }
}