// core/application/use-cases/reservation/UpdateReservation.ts
import { z } from 'zod';
import type { ReservationRepository } from '../../../repositories/product/ReservationRepository';

const UpdateReservationSchema = z.object({
    customerName: z.string().min(2).optional(),
    customerPhone: z.string().min(5).optional(),
    customerEmail: z.string().email().nullable().optional(),
    tableId: z.string().optional(),
    reservationDate: z.string().optional(),
    reservationTime: z.string().optional(),
    status: z.string().optional(),
    partySize: z.number().int().positive().optional(),
    specialRequests: z.string().nullable().optional(),
});

export class UpdateReservation {
    constructor(
        private reservationRepo: ReservationRepository,
    ) {}

    async execute(reservationId: string, input: z.infer<typeof UpdateReservationSchema>) {
        if (!reservationId) throw new Error('شناسه رزرو معتبر نیست');
        const validated = UpdateReservationSchema.parse(input);

        const existing = await this.reservationRepo.findById(reservationId);
        if (!existing) throw new Error('Reservation not found');

        await this.reservationRepo.update(reservationId, validated);
    }
}