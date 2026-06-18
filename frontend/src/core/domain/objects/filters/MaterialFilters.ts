
export interface MaterialFilters {
    search?: string;         // جستجو در name, description
    unit?: string;
    lowStock?: boolean;      // currentStock <= reorderLevel
    isActive?: boolean;      // اگر فیلد isActive دارید (در مدل شما نیست، می‌توانید اضافه کنید)
}