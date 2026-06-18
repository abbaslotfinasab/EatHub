// core/domain/repositories/sales/ReservationRepository.ts
import type { Reservation } from '../../entities/product/Reservation';
import type {ReservationFilters} from "../../objects/filters/ReservationFilters.ts";


export interface ReservationRepository {
    // ذخیره (ایجاد یا به‌روزرسانی) رزرو
    save(reservation: Reservation): Promise<Reservation>;

    // پیدا کردن با شناسه
    findById(id: string): Promise<Reservation | null>;

    // دریافت لیست رزروها با فیلتر
    findAll(filters?: ReservationFilters): Promise<Reservation[]>;

    // به‌روزرسانی جزئی
    update(id: string, data: Partial<Reservation>): Promise<Reservation>;

    // حذف رزرو (فقط در وضعیت PENDING یا CANCELLED مجاز است)
    delete(id: string): Promise<void>;
}