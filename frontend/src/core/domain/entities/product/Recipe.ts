export interface Recipe {
    id?: string;
    name?: string | null; // توضیحات پخت (اختیاری، برای آشپز)
    description?: string | null; // توضیحات پخت (اختیاری، برای آشپز)
    instructions?: string | null; // مواد اولیه بکار رفته در پخت (اختیاری، برای آشپز)
    createdAt?: string;
    updatedAt?: string;
}