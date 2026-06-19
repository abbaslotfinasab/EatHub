// // src/presentation/pages/MaterialsListPage.tsx
// import { useEffect, useState } from 'react';
// import { Link } from 'react-router-dom';
// import { useGetAllMaterials } from '../hooks/useGetAllMaterials';
// import { useDeleteMaterial } from '../hooks/useDeleteMaterial';
// import { useNavbar } from '../hooks/useNavbar';
// import {Plus, Search, Edit, Trash2, ChevronDown, ChevronUp, Package, Coffee, ArrowBigLeft} from 'lucide-react';
//
// export const MaterialsListPage = () => {
//     const { setRightElement, setShowMenu } = useNavbar();
//     const [searchTerm, setSearchTerm] = useState('');
//     const [lowStockOnly, setLowStockOnly] = useState(false);
//     const [isActiveFilter, setIsActiveFilter] = useState<boolean | undefined>(undefined);
//     const [expandedId, setExpandedId] = useState<string | null>(null);
//
//     const filters = {
//         search: searchTerm || undefined,
//         lowStock: lowStockOnly || undefined,
//         isActive: isActiveFilter,
//     };
//
//     const { data: materials = [], isLoading, error } = useGetAllMaterials(filters);
//     const { mutate: deleteMaterial } = useDeleteMaterial();
//
//     useEffect(() => {
//         setShowMenu(false);
//         setRightElement(
//             <button
//                 type="submit"
//                 form="recipe-form"
//                 className="rounded-lg bg-red-500 px-4 py-1.5 text-sm font-semibold text-white hover:bg-red-700"
//             >
//                 <ArrowBigLeft className="ml-1 inline h-4 w-4" />
//                 برگشت
//             </button>
//         );
//         return () => setRightElement(null);
//     }, [setRightElement, setShowMenu]);
//
//     const handleDelete = (id: string, name: string) => {
//         if (window.confirm(`آیا از حذف ماده مرکب "${name}" اطمینان دارید؟`)) {
//             deleteMaterial(id);
//         }
//     };
//
//     const toggleExpand = (id: string) => {
//         setExpandedId(prev => (prev === id ? null : id));
//     };
//
//     // تابع برای استخراج نام و نوع ماده مصرفی (در صورت داشتن نام)
//     const getIngredientDisplay = (ing: any) => {
//         // فرض می‌کنیم در هر MaterialIngredient یکی از ingredientId یا materialId وجود دارد
//         // و همچنین فیلدهای ingredientName/materialName در mock یا API باید پر شود
//         if (ing.ingredientName) return { name: ing.ingredientName, type: 'ingredient', unit: ing.unit };
//         if (ing.materialName) return { name: ing.materialName, type: 'material', unit: ing.unit };
//         // در غیر این صورت، شناسه را نشان بده
//         return { name: ing.ingredientId || ing.materialId || 'نامشخص', type: 'unknown', unit: ing.unit };
//     };
//
//     if (isLoading) return <div className="p-8 text-center">در حال بارگذاری...</div>;
//     if (error) return <div className="p-8 text-center text-red-500">خطا در دریافت اطلاعات</div>;
//
//     return (
//         <div className="mx-auto max-w-7xl px-4 py-6">
//             {/* نوار فیلتر و جستجو */}
//             <div className="mb-6 flex flex-col gap-4 rounded-lg bg-white p-4 shadow-sm md:flex-row md:items-center md:justify-between">
//                 <div className="relative flex-1">
//                     <Search className="absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
//                     <input
//                         type="text"
//                         placeholder="جستجو بر اساس نام، کد SKU، تأمین‌کننده یا دسته..."
//                         className="h-10 w-full rounded-lg border border-gray-300 pr-10 pl-4 text-sm"
//                         value={searchTerm}
//                         onChange={(e) => setSearchTerm(e.target.value)}
//                     />
//                 </div>
//                 <div className="flex flex-wrap items-center gap-3">
//                     <label className="flex items-center gap-2 text-sm">
//                         <input
//                             type="checkbox"
//                             checked={lowStockOnly}
//                             onChange={(e) => setLowStockOnly(e.target.checked)}
//                             className="rounded border-gray-300"
//                         />
//                         موجودی کم (زیر سطح هشدار)
//                     </label>
//                     <select
//                         className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
//                         value={isActiveFilter === undefined ? 'all' : isActiveFilter ? 'active' : 'inactive'}
//                         onChange={(e) => {
//                             const val = e.target.value;
//                             if (val === 'all') setIsActiveFilter(undefined);
//                             else if (val === 'active') setIsActiveFilter(true);
//                             else setIsActiveFilter(false);
//                         }}
//                     >
//                         <option value="all">همه (فعال و غیرفعال)</option>
//                         <option value="active">فعال</option>
//                         <option value="inactive">غیرفعال</option>
//                     </select>
//
//                     <Link
//                         to="/materials/create"
//                         className="inline-flex items-center gap-1 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-red-700"
//                     >
//                         <Plus className="h-4 w-4" />
//                         ماده مرکب جدید
//                     </Link>
//                 </div>
//             </div>
//
//             {/* جدول مواد مرکب */}
//             <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
//                 <div className="overflow-x-auto">
//                     <table className="min-w-full divide-y divide-gray-200">
//                         <thead className="bg-red-50">
//                         <tr>
//                             <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">نام</th>
//                             <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">موجودی(خالص)</th>
//                             <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">واحد</th>
//                             <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">ناخالص</th>
//                             <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">سطح هشدار</th>
//                             <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">مقدار شارژ مجدد</th>
//                             <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">تاریخ انقضا</th>
//                             <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">نوع</th>
//                             <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">وضعیت</th>
//                             <th className="px-6 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">عملیات</th>
//                         </tr>
//                         </thead>
//                         <tbody className="divide-y divide-gray-200 bg-white">
//                         {materials.length === 0 ? (
//                             <tr>
//                                 <td colSpan={7} className="px-6 py-10 text-center text-gray-500">
//                                     هیچ ماده مرکبی یافت نشد.
//                                 </td>
//                             </tr>
//                         ) : (
//                             materials.map((item) => {
//                                 const isExpanded = expandedId === item.material.id;
//                                 return (
//                                     <>
//                                         {/* ردیف اصلی ماده مرکب */}
//                                         <tr
//                                             key={item.material.id}
//                                             className="cursor-pointer hover:bg-gray-50 transition-colors"
//                                             onClick={() => toggleExpand(item.material.id)}
//                                         >
//                                             <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
//                                                 <div className="flex items-center gap-2">
//                                                     {isExpanded ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
//                                                     {item.material.name}
//                                                 </div>
//                                             </td>
//                                             <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{item.material.unit}</td>
//                                             <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
//                           <span className={item.material.currentStock <= item.material.reorderLevel ? 'font-semibold text-red-600' : ''}>
//                             {item.material.currentStock}
//                           </span>
//                                             </td>
//                                             <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">{item.material.reorderLevel}</td>
//                                             <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
//                                                 {item.material.costPrice?.toLocaleString()} تومان
//                                             </td>
//                                             <td className="whitespace-nowrap px-6 py-4 text-sm">
//                           <span
//                               className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
//                                   item.material.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
//                               }`}
//                           >
//                             {item.material.isActive ? 'فعال' : 'غیرفعال'}
//                           </span>
//                                             </td>
//                                             <td className="whitespace-nowrap px-6 py-4 text-center text-sm">
//                                                 <div className="flex items-center justify-center gap-2" onClick={(e) => e.stopPropagation()}>
//                                                     <Link
//                                                         to={`/materials/${item.material.id}/edit`}
//                                                         className="rounded p-1 text-blue-600 hover:bg-blue-50"
//                                                         title="ویرایش"
//                                                     >
//                                                         <Edit className="h-5 w-5" />
//                                                     </Link>
//                                                     <button
//                                                         onClick={(e) => {
//                                                             e.stopPropagation();
//                                                             handleDelete(item.material.id, item.material.name);
//                                                         }}
//                                                         className="rounded p-1 text-red-600 hover:bg-red-50"
//                                                         title="حذف"
//                                                     >
//                                                         <Trash2 className="h-5 w-5" />
//                                                     </button>
//                                                 </div>
//                                             </td>
//                                         </tr>
//
//                                         {/* ردیف‌های مواد تشکیل‌دهنده (در صورت باز بودن و وجود آیتم) */}
//                                         {isExpanded && item.ingredients?.map((ing, idx) => {
//                                             const display = getIngredientDisplay(ing);
//                                             return (
//                                                 <tr key={`${item.material.id}-ing-${idx}`} className="bg-gray-50/70 hover:bg-gray-100">
//                                                     <td className="whitespace-nowrap px-6 py-3 pr-10 text-sm text-gray-700">
//                                                         <div className="flex items-center gap-2">
//                                                             {display.type === 'ingredient' ? (
//                                                                 <Coffee className="h-4 w-4 text-amber-500" />
//                                                             ) : (
//                                                                 <Package className="h-4 w-4 text-emerald-500" />
//                                                             )}
//                                                             <span>↳ {display.name}</span>
//                                                         </div>
//                                                     </td>
//                                                     <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-500">{display.unit}</td>
//                                                     <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-500">{ing.quantity}</td>
//                                                     <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-400" colSpan={1}>—</td>
//                                                     <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-400" colSpan={1}>—</td>
//                                                     <td className="whitespace-nowrap px-6 py-3 text-sm text-gray-400">—</td>
//                                                     <td className="whitespace-nowrap px-6 py-3 text-center text-sm text-gray-400">—</td>
//                                                 </tr>
//                                             );
//                                         })}
//
//                                         {/* پیام خالی بودن مواد */}
//                                         {isExpanded && (!item.ingredients || item.ingredients.length === 0) && (
//                                             <tr className="bg-gray-50/70">
//                                                 <td colSpan={7} className="px-6 py-3 text-center text-sm text-gray-500">
//                                                     این ماده مرکب هیچ ماده مصرفی ندارد.
//                                                 </td>
//                                             </tr>
//                                         )}
//                                     </>
//                                 );
//                             })
//                         )}
//                         </tbody>
//                     </table>
//                 </div>
//             </div>
//         </div>
//     );
// };