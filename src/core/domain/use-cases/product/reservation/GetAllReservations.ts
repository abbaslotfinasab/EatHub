// core/application/use-cases/reservation/GetAllReservations.ts
import type { ReservationRepository } from '../../../repositories/product/ReservationRepository';
import type { Reservation } from '../../../entities/product/Reservation';
import type {ReservationFilters} from "../../../objects/filters/ReservationFilters.ts";


export class GetAllReservations {
    constructor(private reservationRepo: ReservationRepository) {}

    async execute(filters?: ReservationFilters): Promise<Reservation[]> {
        return this.reservationRepo.findAll(filters);
    }
}