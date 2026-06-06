// core/application/use-cases/reservation/DeleteReservation.ts
import type { ReservationRepository } from '../../../repositories/product/ReservationRepository';

export class DeleteReservation {
    constructor(private reservationRepo: ReservationRepository) {}

    async execute(reservationId: string): Promise<void> {
        if (!reservationId) throw new Error('شناسه رزرو معتبر نیست');
        // بک‌اند بررسی می‌کند که فقط رزروهای با وضعیت PENDING یا CANCELLED قابل حذف باشند
        await this.reservationRepo.delete(reservationId);
    }
}