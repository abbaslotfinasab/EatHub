// src/presentation/components/form/PurchaseOrderItemList.tsx
import { useState, useMemo } from 'react';
import { useFormContext, useFieldArray } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { debounce } from 'lodash';
import { Search, X, Trash2, Package } from 'lucide-react';
import { FormInput } from './FormInput';

// ---------- تایپ‌های مربوط به جستجو ----------
interface SearchIngredient {
    id: string;
    name: string;
    unit: string;
}

// ---------- تایپ آیتم فرم (هر ردیف) ----------
interface PurchaseOrderItemFormValue {
    ingredientId: string;
    quantity: number;
    unitPrice: number;
}

// ---------- تایپ کل فرم (برای useFieldArray) ----------
interface FormValues {
    items: PurchaseOrderItemFormValue[];
}

// ---------- تابع جستجو ----------
const searchIngredients = async (searchTerm: string): Promise<SearchIngredient[]> => {
    if (!searchTerm) return [];
    const res = await fetch(`/api/ingredients?search=${encodeURIComponent(searchTerm)}`);
    return res.json();
};

export const PurchaseOrderItemList = () => {
    const { control } = useFormContext<FormValues>();
    // ✅ استفاده از Generic برای useFieldArray
    const { fields, append, remove } = useFieldArray<FormValues, 'items', 'id'>({
        control,
        name: 'items',
    });
    const [searchTerm, setSearchTerm] = useState('');
    const [isOpen, setIsOpen] = useState(false);

    const debouncedSearch = useMemo(
        () =>
            debounce((value: string) => {
                setSearchTerm(value);
                setIsOpen(!!value);
            }, 400),
        []
    );

    const { data, isLoading } = useQuery({
        queryKey: ['ingredients-search', searchTerm],
        queryFn: () => searchIngredients(searchTerm),
        enabled: searchTerm.length > 0,
    });

    // کش به صورت مقدار مشتق شده
    const ingredientCache = useMemo(() => {
        if (!data) return new Map<string, SearchIngredient>();
        const newCache = new Map<string, SearchIngredient>();
        data.forEach((ing) => newCache.set(ing.id, ing));
        return newCache;
    }, [data]);

    const handleAdd = (ing: SearchIngredient) => {
        append({
            ingredientId: ing.id,
            quantity: 1,
            unitPrice: 0,
        });
        setSearchTerm('');
        setIsOpen(false);
    };

    const getIngredientName = (id: string) => ingredientCache.get(id)?.name || id;

    return (
        <div className="space-y-5">
            {/* جستجو */}
            <div className="relative">
                <div className="relative">
                    <Search className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="جستجوی ماده اولیه..."
                        className="h-11 w-full rounded-lg border border-gray-300 bg-white pr-10 pl-10 text-sm shadow-sm focus:border-blue-500 focus:outline-none"
                        onChange={(e) => debouncedSearch(e.target.value)}
                    />
                    {searchTerm && (
                        <button
                            onClick={() => {
                                setSearchTerm('');
                                setIsOpen(false);
                            }}
                            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    )}
                </div>
                {isOpen && (isLoading || data) && (
                    <div className="absolute z-20 mt-2 max-h-60 w-full overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg">
                        {isLoading && <div className="p-3 text-sm text-gray-500">جستجو...</div>}
                        {data?.map((ing) => (
                            <button
                                key={ing.id}
                                type="button"
                                onClick={() => handleAdd(ing)}
                                className="flex w-full justify-between px-3 py-2 text-sm hover:bg-gray-50"
                            >
                                <span>{ing.name}</span>
                                <span className="text-xs text-gray-400">{ing.unit}</span>
                            </button>
                        ))}
                        {data?.length === 0 && <div className="p-3 text-sm text-gray-500">نتیجه‌ای یافت نشد</div>}
                    </div>
                )}
            </div>

            {/* لیست آیتم‌ها */}
            <div className="space-y-3">
                {fields.length === 0 && (
                    <div className="flex flex-col items-center rounded-lg border-2 border-dashed border-gray-200 py-8 text-sm text-gray-400">
                        <Package className="mb-2 h-8 w-8 text-gray-300" />
                        از قسمت جستجو، مواد اولیه را اضافه کنید
                    </div>
                )}

                {fields.map((field, index) => {
                    // ✅ حالا TypeScript می‌داند که field.ingredientId وجود دارد
                    const ingredientName = getIngredientName(field.ingredientId);
                    return (
                        <div key={field.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                                <div className="flex-1">
                                    <div className="mb-1 text-sm font-medium text-gray-700">{ingredientName}</div>
                                    <div className="flex flex-wrap gap-3">
                                        <div className="w-28">
                                            <FormInput
                                                name={`items.${index}.quantity`}
                                                label="مقدار"
                                                type="number"
                                                className="!py-1.5 !text-sm"
                                            />
                                        </div>
                                        <div className="w-36">
                                            <FormInput
                                                name={`items.${index}.unitPrice`}
                                                label="قیمت واحد (تومان)"
                                                type="number"
                                                className="!py-1.5 !text-sm"
                                            />
                                        </div>
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => remove(index)}
                                    className="p-2 text-gray-400 hover:text-red-500"
                                >
                                    <Trash2 className="h-5 w-5" />
                                </button>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};