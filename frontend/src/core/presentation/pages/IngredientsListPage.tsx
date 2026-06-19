// src/presentation/pages/IngredientsListPage.tsx
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useGetAllIngredients } from '../hooks/useGetAllIngredients';
import { useNavbar } from '../hooks/useNavbar';
import {Plus, Search, Edit, Trash2, ArrowBigLeft} from 'lucide-react';

export const IngredientsListPage = () => {
    const {setRightElement, setShowMenu } = useNavbar();
    const [searchTerm, setSearchTerm] = useState('');
    const [lowStockOnly, setLowStockOnly] = useState(false);
    const [isActiveFilter, setIsActiveFilter] = useState<boolean | undefined>(undefined);

    // فیلترها
    const filters = {
        search: searchTerm || undefined,
        lowStock: lowStockOnly || undefined,
        isActive: isActiveFilter,
    };

    const { data: ingredients = [], isLoading, error } = useGetAllIngredients(filters);

    // تنظیم Navbar
    useEffect(() => {
        setShowMenu(false);
        setRightElement(
            <button
                type="submit"
                form="recipe-form"
                className="rounded-lg bg-red-500 px-4 py-1.5 text-sm font-semibold text-white hover:bg-red-700"
            >
                <ArrowBigLeft className="ml-1 inline h-4 w-4" />
                برگشت
            </button>
        );
        return () => {
            setRightElement(null);
        };
    }, [setRightElement, setShowMenu]);




    if (isLoading) return <div className="p-8 text-center">در حال بارگذاری...</div>;
    if (error) return <div className="p-8 text-center text-red-500">خطا در دریافت اطلاعات</div>;

    return (
        <div className="mx-auto max-w-7xl px-4 py-6">
            {/* نوار فیلتر و جستجو */}
            <div className="mb-6 flex flex-col gap-4 rounded-lg bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between">
                <div className="relative flex-1">
                    <Search className="absolute right-3 top-1/2 h-5 w-3 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="جستجو بر اساس نام، کد SKU، تأمین‌کننده یا دسته..."
                        className="h-10 w-full rounded-lg border border-gray-300 pr-10 pl-4 text-sm"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex flex-wrap gap-3">
                    <label className="flex items-center gap-2 text-sm">
                        <input
                            type="checkbox"
                            checked={lowStockOnly}
                            onChange={(e) => setLowStockOnly(e.target.checked)}
                            className="rounded border-gray-300"
                        />
                        موجودی کم (زیر سطح هشدار)
                    </label>
                    <select
                        className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
                        value={isActiveFilter === undefined ? 'all' : isActiveFilter ? 'active' : 'inactive'}
                        onChange={(e) => {
                            const val = e.target.value;
                            if (val === 'all') setIsActiveFilter(undefined);
                            else if (val === 'active') setIsActiveFilter(true);
                            else setIsActiveFilter(false);
                        }}
                    >
                        <option value="all">همه (فعال و غیرفعال)</option>
                        <option value="active">فعال</option>
                        <option value="inactive">غیرفعال</option>
                    </select>

                    <Link
                        to="/ingredients/create"
                        className="inline-flex items-center gap-1 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-red-700"
                    >
                        <Plus className="h-4 w-4" />
                        ماده جدید
                    </Link>

                </div>
            </div>

            {/* جدول مواد اولیه */}
            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-red-50">
                        <tr>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">نام</th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">موجودی</th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">واحد</th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">سطج هشدار</th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">مقدار خرید مجدد</th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">تاریخ انقضا</th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">نوع</th>
                            <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">وضعیت</th>
                            <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">عملیات</th>
                        </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                        {ingredients.length === 0 ? (
                            <tr>
                                <td colSpan={7} className="px-6 py-10 text-center text-gray-500">
                                    هیچ ماده اولیه‌ای یافت نشد.
                                </td>
                            </tr>
                        ) : (
                            ingredients.map((ing) => (
                                <tr key={ing.id} className="hover:bg-gray-50">
                                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">{ing.name}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      <span className={ing.currentStock <= ing.reorderLevel ? 'font-semibold text-red-600' : ''}>
                        {ing.currentStock}
                      </span>
                                    </td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{ing.unit}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{ing.reorderLevel}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{ing.reorderQuantity}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{ing.reorderQuantity}</td>

                                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <span
                          className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                              ing.complete
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-orange-100 text-orange-800'
                          }`}
                      >
                        {ing.complete ? 'آماده' : 'نبمه آماده'}
                      </span>
                                    </td>

                                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      <span
                          className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                              ing.isActive
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                          }`}
                      >
                        {ing.isActive ? 'فعال' : 'غیر فعال'}
                      </span>
                                    </td>

                                    <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
                                        <div className="flex items-center justify-center gap-2">
                                            <Link
                                                to={`/ingredients/${ing.id}/edit`}
                                                className="rounded p-1 text-blue-600 hover:bg-blue-50"
                                                title="ویرایش"
                                            >
                                                <Edit className="h-5 w-5" />
                                            </Link>
                                            <button
                                                className="rounded p-1 text-red-600 hover:bg-red-50"
                                                title="حذف"
                                            >
                                                <Trash2 className="h-5 w-5" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};