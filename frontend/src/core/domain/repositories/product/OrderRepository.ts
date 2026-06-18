// core/domain/repositories/sales/OrderRepository.ts
import type { Order } from '../../entities/product/Order';
import type {OrderItem} from "../../entities/product/OrderItem.ts";
import type {OrderResult} from "../../entities/product/OrderResult.ts";
import type {OrderFilters} from "../../objects/filters/OrderFilters.ts";


export interface OrderRepository {
    // ذخیره سفارش به همراه آیتم‌ها (تراکنشی)
    create(
        order: Omit<Order, 'id' | 'createdAt' | 'updatedAt'  | 'tax' | 'customerName' | 'status' | 'totalAmount' | 'subtotal' | 'discount'>,
        items: Omit<OrderItem, 'id' | 'createdAt' | 'updatedAt'>[]
    ): Promise<OrderResult>;

    // پیدا کردن سفارش با شناسه (بدون آیتم‌ها)
    findById(id: string): Promise<OrderResult | null>;

    // دریافت لیست سفارش‌ها با فیلتر (بدون آیتم‌ها)
    findAll(filters?: OrderFilters): Promise<OrderResult[]>;

    // به‌روزرسانی جزئی فیلدهای سفارش
// در اینترفیس OrderRepository
    update(
        orderId: string,
        orderData: Partial<Omit<Order, 'id' | 'createdAt' | 'updatedAt'>>,
        items?: Omit<OrderItem, 'id' | 'orderId' | 'createdAt' | 'updatedAt'>[] // در صورت ارسال، جایگزین کامل
    ): Promise<OrderResult>;

    // حذف سفارش (فقط در وضعیت‌های خاص مثل PENDING یا CANCELLED)
    delete(id: string): Promise<void>;
}