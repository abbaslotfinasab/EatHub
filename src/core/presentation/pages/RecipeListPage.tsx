// src/presentation/pages/RecipeListPage.tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useGetAllRecipes } from '../hooks/useGetAllRecipes';
import { useDeleteRecipe } from '../hooks/useDeleteRecipe';
import { useNavbar } from '../hooks/useNavbar';
import { Plus, Search, Edit, Trash2, ChevronDown, ChevronUp, Package, Coffee } from 'lucide-react';

export const RecipeListPage = () => {
    const { setRightElement, setShowMenu } = useNavbar();
    const [searchTerm, setSearchTerm] = useState('');
    const [expandedId, setExpandedId] = useState<string | null>(null);
    // در صورت نیاز فیلترهای دیگر مثل وضعیت فعال می‌توان اضافه کرد

    const filters = {
        search: searchTerm || undefined,
    };

    const { data: recipes = [], isLoading, error } = useGetAllRecipes(filters);
    const { mutate: deleteRecipe } = useDeleteRecipe();

    useEffect(() => {
        setShowMenu(true);
        setRightElement(
            <Link
                to="/recipes/create"
                className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-700"
            >
                <Plus className="h-4 w-4" />
                رسپی جدید
            </Link>
        );
        return () => {
            setRightElement(null);
        };
    }, [setRightElement, setShowMenu]);

    const handleDelete = (id: string, name: string) => {
        if (window.confirm(`آیا از حذف رسپی "${name}" اطمینان دارید؟`)) {
            deleteRecipe(id);
        }
    };

    const toggleExpand = (id: string) => {
        setExpandedId(prev => (prev === id ? null : id));
    };

    // تابع برای استخراج نام و نوع ماده مصرفی (با فرض وجود ingredientName/materialName)
    const getIngredientDisplay = (ing: any) => {
        if (ing.ingredientName) return { name: ing.ingredientName, type: 'ingredient', unit: ing.unit };
        if (ing.materialName) return { name: ing.materialName, type: 'material', unit: ing.unit };
        // در صورت نبود نام، از شناسه استفاده می‌کنیم
        return { name: ing.ingredientId || ing.materialId || 'نامشخص', type: 'unknown', unit: ing.unit };
    };

    if (isLoading) return <div className="p-8 text-center">در حال بارگذاری...</div>;
    if (error) return <div className="p-8 text-center text-red-500">خطا در دریافت اطلاعات</div>;

    return (
        <div className="mx-auto max-w-7xl px-4 py-6">
            {/* نوار جستجو */}
            <div className="mb-6 flex flex-col gap-4 rounded-lg bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between">
                <div className="relative flex-1">
                    <Search className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="جستجو بر اساس نام رسپی..."
                        className="h-10 w-full rounded-lg border border-gray-300 pr-10 pl-4 text-sm"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {/* جدول رسپی‌ها */}
            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">نام</th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">تعداد خروجی</th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">توضیحات</th>
                            <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">عملیات</th>
                        </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                        {recipes.length === 0 ? (
                            <tr>
                                <td colSpan={4} className="px-6 py-10 text-center text-gray-500">
                                    هیچ رسپی‌ای یافت نشد.
                                </td>
                            </tr>
                        ) : (
                            recipes.map((item) => {
                                const isExpanded = expandedId === item.recipe.id;
                                return (
                                    <>
                                        {/* ردیف اصلی رسپی */}
                                        <tr
                                            key={item.recipe.id}
                                            className="cursor-pointer hover:bg-gray-50 transition-colors"
                                            onClick={() => toggleExpand(item.recipe.id)}
                                        >
                                            <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                                                <div className="flex items-center gap-2">
                                                    {isExpanded ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
                                                    {item.recipe.name}
                                                </div>
                                            </td>
                                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{item.recipe.yield} پرس</td>
                                            <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 truncate max-w-xs">{item.recipe.description || '—'}</td>
                                            <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                                                <div className="flex items-center justify-center gap-2" onClick={(e) => e.stopPropagation()}>
                                                    <Link
                                                        to={`/recipes/${item.recipe.id}/edit`}
                                                        className="rounded p-1 text-blue-600 hover:bg-blue-50"
                                                        title="ویرایش"
                                                    >
                                                        <Edit className="h-5 w-5" />
                                                    </Link>
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDelete(item.recipe.id, item.recipe.name);
                                                        }}
                                                        className="rounded p-1 text-red-600 hover:bg-red-50"
                                                        title="حذف"
                                                    >
                                                        <Trash2 className="h-5 w-5" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>

                                        {/* ردیف‌های مواد مصرفی (در صورت باز بودن و وجود آیتم) */}
                                        {isExpanded && item.ingredients?.map((ing, idx) => {
                                            const display = getIngredientDisplay(ing);
                                            return (
                                                <tr key={`${item.recipe.id}-ing-${idx}`} className="bg-gray-50/70 hover:bg-gray-100">
                                                    <td className="whitespace-nowrap px-6 py-3 pr-10 text-sm text-gray-700">
                                                        <div className="flex items-center gap-2">
                                                            {display.type === 'ingredient' ? (
                                                                <Coffee className="h-4 w-4 text-amber-500" />
                                                            ) : (
                                                                <Package className="h-4 w-4 text-emerald-500" />
                                                            )}
                                                            <span>↳ {display.name}</span>
                                                        </div>
                                                    </td>
                                                    <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-500">
                                                        {ing.quantity} {display.unit}
                                                    </td>
                                                    <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-400" colSpan={2}>—</td>
                                                </tr>
                                            );
                                        })}

                                        {/* پیام خالی بودن مواد */}
                                        {isExpanded && (!item.ingredients || item.ingredients.length === 0) && (
                                            <tr className="bg-gray-50/70">
                                                <td colSpan={4} className="px-6 py-3 text-center text-sm text-gray-500">
                                                    این رسپی هیچ ماده مصرفی ندارد.
                                                </td>
                                            </tr>
                                        )}
                                    </>
                                );
                            })
                        )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};