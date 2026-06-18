// core/domain/repositories/sales/TableRepository.ts
import type { Table } from '../../entities/product/Table';
import type {TableFilters} from "../../objects/filters/TableFilters.ts";


export interface TableRepository {
    // ایجاد میز جدید
    save(table: Table): Promise<Table>;

    // پیدا کردن میز با شناسه
    findById(id: string): Promise<Table | null>;

    // دریافت لیست میزها با فیلتر
    findAll(filters?: TableFilters): Promise<Table[]>;

    // به‌روزرسانی اطلاعات میز
    update(id: string, data: Partial<Table>): Promise<Table>;

    // حذف میز (فقط در صورت عدم وجود وابستگی)
    delete(id: string): Promise<void>;

    // (اختیاری) بررسی در دسترس بودن یک میز خاص در بازه زمانی
    isTableAvailable(tableId: string, date: string, startTime: string, endTime: string, excludeReservationId?: string): Promise<boolean>;

}