// core/domain/repositories/sales/OrderRepository.ts
import type {OrderWithItems} from "../../entities/product/order/OrderWithItems.ts";
import type {UpdateOrderStatusInput} from "../../entities/product/order/UpdateOrderStatusInput.ts";


export interface OrderRepository {
    // ذخیره سفارش به همراه آیتم‌ها (تراکنشی)
    create(
        input: OrderWithItems
    ): Promise<void>;


    // پیدا کردن سفارش با شناسه (بدون آیتم‌ها)
    findById(id: string): Promise<OrderWithItems | null>;

    // دریافت لیست سفارش‌ها با فیلتر (بدون آیتم‌ها)
    findAll(): Promise<OrderWithItems[]>;

    // به‌روزرسانی جزئی فیلدهای سفارش
// در اینترفیس OrderRepository
    update(
        id: string,
        order: OrderWithItems,
    ): Promise<void>;

    // حذف سفارش (فقط در وضعیت‌های خاص مثل PENDING یا CANCELLED)
    delete(id: string): Promise<void>;

     updateStatus(
        input: UpdateOrderStatusInput,
    ): Promise<void>;
}