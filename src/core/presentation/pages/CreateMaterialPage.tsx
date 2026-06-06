// src/presentation/pages/CreateMaterialPage.tsx
import { zodResolver } from '@hookform/resolvers/zod';
import { FormProvider, useForm } from 'react-hook-form';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateMaterial } from '../hooks/useCreateMaterial';
import { useNavbar } from '../hooks/useNavbar';
import { FormInput } from '../components/form/FormInput';
import { IngredientList } from '../components/form/IngredientList';
import {Save, Package, Info, ArrowBigLeft} from 'lucide-react';
import {
    type CreateMaterialWithIngredientsInput, CreateMaterialWithIngredientsSchema
} from "../../domain/use-cases/inventory/material/CreateMaterialWithIngredients.ts";
import {Unit} from "../../domain/objects/unit.ts";
import {FormSelect} from "../components/form/FormSelect.tsx";
import {FormTextarea} from "../components/form/FormTextarea.tsx";

export const CreateMaterialPage = () => {
    const navigate = useNavigate();
    const {setRightElement, setShowMenu } = useNavbar();
    const { mutate: createMaterial } = useCreateMaterial();

    const methods = useForm({
        resolver: zodResolver(CreateMaterialWithIngredientsSchema),
        defaultValues: {
            name: '',
            description: null,           // ✅ مطابق با nullable
            unitId: '',
            currentStock: 0,
            reorderLevel: 0,
            reorderQuantity: 1,
            costPrice: 0,
            ingredients: [],
        },
    });

    useEffect(() => {
        setShowMenu(false);
        setRightElement(
            <button
                type="submit"
                form="material-form"
                className="rounded-lg bg-red-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-red-700"
            >
                <ArrowBigLeft className="ml-1 inline h-4 w-4" />
                برگشت
            </button>
        );
        return () => {
            setShowMenu(true);
            setRightElement(null);
        };
    }, [setRightElement, setShowMenu]);

    const onSubmit = (data: CreateMaterialWithIngredientsInput) => {
        createMaterial(data, {
            onSuccess: () => navigate('/materials'),
        });
    };

    return (
        <FormProvider {...methods}>
            <form id="material-form" onSubmit={methods.handleSubmit(onSubmit)}>
                <div className="mx-auto max-w-5xl px-4 py-8">
                    <div className="overflow-hidden rounded-xl border-2 border-t-red-600 bg-white shadow-sm">
                        {/* هدر کارت با عنوان و دکمه */}
                        <div className="border-b border-gray-100 px-6 py-4">
                            <div className="flex items-center justify-between">
                                <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-800">
                                    <Package className="h-5 w-5 text-blue-500" />
                                    اطلاعات ماده مرکب
                                </h2>
                                <button
                                    type="submit"
                                    form="material-form"
                                    className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
                                >
                                    <Save className="ml-1 inline h-4 w-4" />
                                    ذخیره
                                </button>
                            </div>
                        </div>

                        <div className="space-y-8 p-6">
                            {/* بخش اطلاعات پایه */}
                            <section>
                                <div className="mb-4 flex items-center gap-2 border-b border-gray-200 pb-2">
                                    <Info className="h-5 w-5 text-blue-500" />
                                    <h3 className="text-base font-semibold text-gray-800">اطلاعات پایه</h3>
                                </div>
                                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                                    <FormInput name="name" label="نام ماده مرکب *" placeholder="مثلاً سس مایونز خانگی" />
                                    <FormInput name="currentStock" label="مقدار موجودی"  type="number" />
                                    <FormSelect
                                        name="unit"
                                        label="واحد *"
                                        options={Object.entries(Unit).map(([value]) => ({
                                            value,
                                            label: '',
                                        }))}
                                    />
                                    <FormInput name="reorderLevel" label="سطح هشدار موجودی" type="number" />
                                    <FormInput name="reorderQuantity" label="مقدار پیشنهادی خرید" type="number" />
                                    <FormInput name="costPrice" label="قیمت تمام‌شده (تومان)" type="number" />
                                </div>

                                <div className="grid grid-cols-1 gap-5 md:grid-cols-1 mt-6">
                                    <FormTextarea name="description" label="توضیحات" rows={3} />
                                </div>

                            </section>

                            {/* بخش مواد مصرفی */}
                            <section>
                                <div className="mb-4 flex items-center gap-2 border-b border-gray-200 pb-2">
                                    <Package className="h-5 w-5 text-emerald-500" />
                                    <h3 className="text-base font-semibold text-gray-800">مواد مصرفی</h3>
                                </div>
                                <IngredientList />
                            </section>
                        </div>
                    </div>
                </div>
            </form>
        </FormProvider>
    );
};