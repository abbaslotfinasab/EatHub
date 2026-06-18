// src/presentation/components/form/IngredientList.tsx
import { useState, useMemo } from 'react';
import { useFormContext, useFieldArray } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { debounce } from 'lodash';
import { Search, X, Trash2, Package, Coffee } from 'lucide-react';
import { FormInput } from './FormInput';

// ---------- تایپ‌های جستجو ----------
interface SearchIngredient {
    id: string;
    name: string;
    unit: string;
}

interface SearchMaterial {
    id: string;
    name: string;
    unit: string;
}

interface SearchResponse {
    ingredients: SearchIngredient[];
    materials: SearchMaterial[];
}

// ---------- تایپ آیتم فرم ----------
export interface IngredientFormItem {
    ingredientId?: string;
    materialId?: string;
    quantity: number;
    unit: string;
    substituteIngredientId?: string | null;
    substituteMaterialId?: string | null;
}

interface FormValues {
    ingredients: IngredientFormItem[];
}

// ---------- تابع جستجو ----------
const searchItems = async (searchTerm: string): Promise<SearchResponse> => {
    if (!searchTerm) return { ingredients: [], materials: [] };
    const [ingredientsRes, materialsRes] = await Promise.all([
        fetch(`/api/ingredients?search=${encodeURIComponent(searchTerm)}`),
        fetch(`/api/materials?search=${encodeURIComponent(searchTerm)}`),
    ]);
    const ingredients: SearchIngredient[] = await ingredientsRes.json();
    const materials: SearchMaterial[] = await materialsRes.json();
    return { ingredients, materials };
};

export const IngredientList = () => {
    const { control } = useFormContext<FormValues>();
    const { fields, append, remove } = useFieldArray<FormValues, 'ingredients', 'id'>({
        control,
        name: 'ingredients',
    });

    const [searchTerm, setSearchTerm] = useState('');
    const [isOpen, setIsOpen] = useState(false);

    // ✅ استفاده از useMemo به جای useCallback (رفع خطای اول)
    const debouncedSearch = useMemo(
        () =>
            debounce((value: string) => {
                setSearchTerm(value);
                setIsOpen(!!value);
            }, 400),
        [] // خالی: فقط یکبار ساخته شود
    );

    const { data, isLoading } = useQuery({
        queryKey: ['search', searchTerm],
        queryFn: () => searchItems(searchTerm),
        enabled: searchTerm.length > 0,
    });

    // ✅ محاسبه کش به عنوان مقدار مشتق شده (رفع خطای setState در effect)
    const materialCache = useMemo(() => {
        if (!data) return new Map<string, { name: string; unit: string }>();
        const newCache = new Map<string, { name: string; unit: string }>();
        data.ingredients.forEach((ing) => {
            newCache.set(ing.id, { name: ing.name, unit: ing.unit });
        });
        data.materials.forEach((mat) => {
            newCache.set(mat.id, { name: mat.name, unit: mat.unit });
        });
        return newCache;
    }, [data]);

    const handleAdd = (item: SearchIngredient | SearchMaterial, type: 'ingredient' | 'material') => {
        const fieldName = type === 'ingredient' ? 'ingredientId' : 'materialId';
        append({
            [fieldName]: item.id,
            quantity: 1,
            unit: item.unit,
            substituteIngredientId: null,
            substituteMaterialId: null,
        });
        setSearchTerm('');
        setIsOpen(false);
    };

    const getMaterialName = (id: string): string => {
        return materialCache.get(id)?.name || id;
    };

    const getMaterialUnit = (id: string): string => {
        return materialCache.get(id)?.unit || '';
    };

    return (
        <div className="space-y-5">
            {/* بخش جستجو */}
            <div className="relative">
                <div className="relative">
                    <Search className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="جستجوی ماده اولیه (Ingredient) یا مواد مرکب (Material)..."
                        className="h-11 w-full rounded-lg border border-gray-300 bg-white pr-10 pl-10 text-sm shadow-sm transition focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        onChange={(e) => debouncedSearch(e.target.value)}
                    />
                    {searchTerm && (
                        <button
                            type="button"
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
                    <div className="absolute z-20 mt-2 max-h-80 w-full overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg">
                        {isLoading && <div className="p-3 text-sm text-gray-500">جستجو...</div>}
                        {data && (
                            <>
                                {data.ingredients.length > 0 && (
                                    <div>
                                        <div className="sticky top-0 flex items-center gap-2 bg-gray-100 px-3 py-2 text-xs font-semibold text-gray-600">
                                            <Coffee className="h-3.5 w-3.5" />
                                            <span>مواد اولیه (Ingredient)</span>
                                        </div>
                                        {data.ingredients.map((ing) => (
                                            <button
                                                key={ing.id}
                                                type="button"
                                                onClick={() => handleAdd(ing, 'ingredient')}
                                                className="flex w-full items-center justify-between px-3 py-2 text-right text-sm transition hover:bg-gray-50"
                                            >
                                                <span>{ing.name}</span>
                                                <span className="text-xs text-gray-400">{ing.unit}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}
                                {data.materials.length > 0 && (
                                    <div className="border-t">
                                        <div className="sticky top-0 flex items-center gap-2 bg-gray-100 px-3 py-2 text-xs font-semibold text-gray-600">
                                            <Package className="h-3.5 w-3.5" />
                                            <span>مواد مرکب (Material)</span>
                                        </div>
                                        {data.materials.map((mat) => (
                                            <button
                                                key={mat.id}
                                                type="button"
                                                onClick={() => handleAdd(mat, 'material')}
                                                className="flex w-full items-center justify-between px-3 py-2 text-right text-sm transition hover:bg-gray-50"
                                            >
                                                <span>{mat.name}</span>
                                                <span className="text-xs text-gray-400">{mat.unit}</span>
                                            </button>
                                        ))}
                                    </div>
                                )}
                                {data.ingredients.length === 0 && data.materials.length === 0 && (
                                    <div className="p-3 text-center text-sm text-gray-500">نتیجه‌ای یافت نشد</div>
                                )}
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* لیست مواد انتخاب شده */}
            <div className="space-y-3">
                {fields.length === 0 && (
                    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 py-8 text-center text-sm text-gray-400">
                        <Package className="mb-2 h-8 w-8 text-gray-300" />
                        <span>از قسمت جستجو، مواد مورد نظر را اضافه کنید</span>
                    </div>
                )}

                {fields.map((field, index) => {
                    const isIngredient = 'ingredientId' in field && field.ingredientId;
                    const itemId = isIngredient ? field.ingredientId : field.materialId;
                    const itemName = itemId ? getMaterialName(itemId) : 'نامشخص';
                    const itemUnit = itemId ? getMaterialUnit(itemId) : '';

                    return (
                        <div
                            key={field.id}
                            className="group rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all hover:shadow-md"
                        >
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                                <div className="flex-1">
                                    <div className="mb-1 flex items-center gap-2">
                                        {isIngredient ? (
                                            <Coffee className="h-4 w-4 text-amber-500" />
                                        ) : (
                                            <Package className="h-4 w-4 text-emerald-500" />
                                        )}
                                        <span className="text-sm font-medium text-gray-700">{itemName}</span>
                                        <span className="text-xs text-gray-400">({isIngredient ? 'Ingredient' : 'Material'})</span>
                                        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                                            {itemUnit}
                                        </span>
                                    </div>
                                    <div className="flex flex-wrap gap-3">
                                        <div className="w-28">
                                            <FormInput
                                                name={`ingredients.${index}.quantity`}
                                                label="مقدار"
                                                type="number"
                                                className="!py-1.5 !text-sm"
                                            />
                                        </div>
                                    </div>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => remove(index)}
                                    className="self-start rounded-md p-2 text-gray-400 transition hover:bg-red-50 hover:text-red-500 sm:self-center"
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