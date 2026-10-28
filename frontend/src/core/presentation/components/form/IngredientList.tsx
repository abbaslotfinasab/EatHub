import { useEffect, useRef, useState } from "react";
import { useFieldArray, useFormContext } from "react-hook-form";
import { useQuery } from "@tanstack/react-query";
import { debounce } from "lodash";
import { Search, Trash2, Coffee, Star } from "lucide-react";
import { FormInput } from "./FormInput";
import { apiClient } from "../../../data/http/http-client";
import { useAuthStore } from "../../store/auth.store";

interface InventoryItem {
    id: number;
    name: string;
    unit: string;
    preparation_level: "raw" | "semi_prepared";
}

interface InventoryPage {
    results: InventoryItem[];
}

export interface RecipeLineFormValue {
    ingredientId: string;
    ingredientName?: string;
    materialType?: "raw" | "compound";
    quantity: string | number;
    unit: string;
    isPrimary?: boolean;
}

interface RecipeFormValues {
    ingredients: RecipeLineFormValue[];
    outputs: RecipeLineFormValue[];
}

interface IngredientListProps {
    fieldName?: "ingredients" | "outputs";
    heading?: string;
    outputMode?: boolean;
    quantityAsText?: boolean;
    preventDuplicates?: boolean;
}

const unitLabels: Record<string, string> = {
    kg: "کیلوگرم", g: "گرم", l: "لیتر", ml: "میلی‌لیتر", pc: "عدد", pk: "بسته",
};

export const IngredientList = ({ fieldName = "ingredients", heading, outputMode = false, quantityAsText = false, preventDuplicates = false }: IngredientListProps) => {
    const { control, watch, setValue } = useFormContext<RecipeFormValues>();
    const me = useAuthStore((state) => state.me);
    const { fields, append, remove } = useFieldArray({ control, name: fieldName });
    const lines = (watch(fieldName) ?? []) as RecipeLineFormValue[];
    const [searchInput, setSearchInput] = useState("");
    const [searchTerm, setSearchTerm] = useState("");
    const debouncedSearch = useRef<ReturnType<typeof debounce> | null>(null);
    useEffect(() => {
        debouncedSearch.current = debounce((value: string) => setSearchTerm(value.trim()), 350);
        return () => debouncedSearch.current?.cancel();
    }, []);

    const query = useQuery({
        queryKey: ["recipe-inventory-items", me?.id ?? null, me?.active_business?.id ?? null, searchTerm],
        enabled: searchTerm.length > 0,
        queryFn: async () => (await apiClient.get<InventoryPage>("/inventory/items/", {
            params: { page_size: 50, is_active: true, search: searchTerm },
        })).data.results,
    });
    const selectedIds = new Set(lines.map((line) => line.ingredientId));

    const handleSearch = (value: string) => {
        setSearchInput(value);
        debouncedSearch.current?.(value);
    };

    const handleAdd = (item: InventoryItem) => {
        const newLine: RecipeLineFormValue = {
            ingredientId: String(item.id),
            ingredientName: item.name,
            materialType: item.preparation_level === "semi_prepared" ? "compound" : "raw",
            quantity: quantityAsText ? "1" : 1,
            unit: item.unit,
        };
        append((outputMode ? { ...newLine, isPrimary: false } : newLine) as never);
        setSearchInput("");
        setSearchTerm("");
    };

    const setPrimary = (lineIndex: number) => {
        const current = (watch("outputs") ?? []) as RecipeLineFormValue[];
        setValue("outputs", current.map((line, index) => ({
            ...line,
            isPrimary: index === lineIndex ? !line.isPrimary : false,
        })), { shouldDirty: true, shouldValidate: true });
    };

    return (
        <div className="space-y-5">
            {heading && <h2 className="text-lg font-semibold text-gray-800">{heading}</h2>}
            <div className="relative">
                <Search className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                <input
                    type="text"
                    placeholder={outputMode ? "جستجوی محصول خروجی از اقلام انبار..." : "جستجوی ماده اولیه انبار..."}
                    aria-label={outputMode ? "جستجوی محصول خروجی" : "جستجوی ماده اولیه"}
                    className="h-11 w-full rounded-lg border border-gray-300 bg-white pr-10 pl-4 text-sm shadow-sm focus:border-blue-500 focus:outline-none"
                    value={searchInput}
                    onChange={(event) => handleSearch(event.target.value)}
                />
                {!!searchTerm && (
                    <div className="absolute z-20 mt-2 max-h-80 w-full overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg">
                        {query.isLoading && <div className="p-3 text-sm text-gray-500">جستجو...</div>}
                        {query.isError && <div className="p-3 text-sm text-red-600">جستجوی اقلام ناموفق بود. دسترسی و اتصال را بررسی کنید.</div>}
                        {query.data?.map((item) => {
                            const alreadySelected = preventDuplicates && selectedIds.has(String(item.id));
                            return (
                                <button
                                    key={item.id}
                                    type="button"
                                    disabled={alreadySelected}
                                    onClick={() => handleAdd(item)}
                                    className="flex w-full items-center justify-between px-3 py-2 text-right text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                                >
                                    <span>{item.name}{alreadySelected ? " — انتخاب شده" : ""}</span>
                                    <span className="text-xs text-gray-400">{unitLabels[item.unit] ?? item.unit}</span>
                                </button>
                            );
                        })}
                        {!query.isLoading && !query.isError && query.data?.length === 0 && (
                            <div className="p-3 text-center text-sm text-gray-500">نتیجه‌ای یافت نشد</div>
                        )}
                    </div>
                )}
            </div>

            <div className="space-y-3">
                {fields.length === 0 && (
                    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 py-8 text-center text-sm text-gray-400">
                        <Coffee className="mb-2 h-8 w-8 text-gray-300" />
                        <span>{outputMode ? "محصول خروجی را از اقلام انبار انتخاب کنید" : "مواد اولیهٔ این دستور را از موجودی انبار انتخاب کنید"}</span>
                    </div>
                )}
                {fields.map((field, index) => {
                    const line = lines[index] ?? field;
                    return (
                        <div key={field.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                                <div className="flex-1">
                                    <div className="mb-2 flex flex-wrap items-center gap-2">
                                        <Coffee className="h-4 w-4 text-amber-500" />
                                        <span className="text-sm font-medium text-gray-700">{line.ingredientName ?? `ماده #${line.ingredientId}`}</span>
                                        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-800">{line.materialType === "compound" ? "مواد مرکب" : "مواد اولیه"}</span>
                                        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">{unitLabels[line.unit] ?? line.unit}</span>
                                        {outputMode && (
                                            <button
                                                type="button"
                                                aria-pressed={Boolean(line.isPrimary)}
                                                onClick={() => setPrimary(index)}
                                                className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs ${line.isPrimary ? "bg-amber-100 text-amber-800" : "bg-gray-100 text-gray-600"}`}
                                            >
                                                <Star className="h-3 w-3" />
                                                {line.isPrimary ? "محصول اصلی" : "انتخاب به‌عنوان محصول اصلی"}
                                            </button>
                                        )}
                                    </div>
                                    <div className="w-40">
                                        <FormInput
                                            name={`${fieldName}.${index}.quantity`}
                                            label="مقدار"
                                            type={quantityAsText ? "text" : "number"}
                                            {...(quantityAsText ? { inputMode: "decimal" as const } : {})}
                                            className="!py-1.5 !text-sm"
                                        />
                                    </div>
                                </div>
                                <button type="button" onClick={() => remove(index)} aria-label="حذف ردیف" className="self-start rounded-md p-2 text-gray-400 hover:bg-red-50 hover:text-red-500 sm:self-center">
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
