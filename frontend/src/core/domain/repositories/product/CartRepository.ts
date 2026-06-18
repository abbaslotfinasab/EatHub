// core/domain/repositories/sales/CartRepository.ts
import type {CartItem} from "../../entities/product/CartItem.ts";
import type {CartResult} from "../../entities/product/CartResult.ts";
import type {Order} from "../../entities/product/Order.ts";

export interface CartRepository {
    // افزودن یک آیتم به سبد فعال (در صورت نبود سبد، آن را ایجاد می‌کند)
    addItem(cartItem:Omit<CartItem, 'id' | 'cartId' | 'totalPrice' | 'unitPrice' | 'createdAt' | 'updatedAt'>): Promise<CartResult>; // برگرداندن سبد به‌روز شده با تمام آیتم‌ها

    // دریافت سبد فعال (برای نمایش)
    getActive(): Promise<CartResult | null>;

    // به‌روزرسانی تعداد یک آیتم خاص
    updateItemQuantity(cartItemId: string, quantity: number): Promise<CartResult>;

    // حذف یک آیتم از سبد
    removeItem(cartItemId: string): Promise<void>;

    // خالی کردن سبد (حذف همه آیتم‌ها)
    clear(cartId: string): Promise<void>;

    // تبدیل سبد به سفارش (نهایی‌سازی)
    checkout(cartId: string): Promise<{ order: Order; paymentUrl?: string }>;

    // (اختیاری) حذف سبد (در صورت لغو کامل)
    delete(cartId: string): Promise<void>;
}