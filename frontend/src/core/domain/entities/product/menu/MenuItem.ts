// core/domain/entities/sales/MenuItem.ts
export interface MenuItem {
    id?: string;
    name: string;
    description: string | null;
    price: number;               // قیمت فروش (تومان/ریال)
    imageUrl: string | null ;
    imageFile: File | null;
    menuId: string;          // ارجاع به Menu
    isAvailable: boolean;        // موجود در منو (می‌تواند به موجودی انبار وابسته باشد)
    createdAt: string;
    updatedAt: string;
}