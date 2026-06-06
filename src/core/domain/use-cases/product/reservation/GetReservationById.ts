// core/application/use-cases/reservation/GetReservationById.ts
import type { ReservationRepository } from '../../../repositories/product/ReservationRepository';

export class GetReservationById {
    constructor(private reservationRepo: ReservationRepository) {}

    async execute(id: string) {
        if (!id) throw new Error('شناسه رزرو معتبر نیست');
        return this.reservationRepo.findById(id);
    }
}