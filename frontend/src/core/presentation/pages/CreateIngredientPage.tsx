// src/presentation/pages/CreateIngredientPage.tsx
import { zodResolver } from '@hookform/resolvers/zod';
import { FormProvider, useForm } from 'react-hook-form';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNavbar } from '../hooks/useNavbar';
import { FormInput } from '../components/form/FormInput';
import {Save, Package, ArrowBigLeft} from 'lucide-react';
import {Unit} from "../../domain/objects/unit.ts";
// ✅ صحیح
import { CreateIngredientSchema, type CreateIngredientInput } from "../../domain/use-cases/inventory/ingredient/CreateIngredient.ts";import {useCreateIngredient} from "../hooks/useCreateIngredient.ts";
import {FormSelect} from "../components/form/FormSelect.tsx";
import {FormSwitch} from "../components/form/FormSwitchProps.tsx";

export const CreateIngredientPage = () => {
    const navigate = useNavigate();
    const {setRightElement, setShowMenu } = useNavbar();
    const { mutate: createIngredient } = useCreateIngredient();

    const methods = useForm<CreateIngredientInput>({
        resolver: zodResolver(CreateIngredientSchema),
        defaultValues: {
            name: '',
            unit: Unit.KG,
            currentStock: 0,
            reorderLevel: 0,
            reorderQuantity: 1,
            costPrice: 0,
            isActive: true,
            categoryId: '',
            complete: false,
            sku: null,
        },
    });

    const { handleSubmit } = methods;

    useEffect(() => {
        setShowMenu(false); // مخفی کردن منوی نوار (فقط لوگو و دکمه)
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
            setShowMenu(true);
            setRightElement(null);
        };
    }, [setRightElement, setShowMenu]);

    const onSubmit = (data: CreateIngredientInput) => {
        createIngredient(data, {
            onSuccess: () => navigate('/ingredients'),
        });
    };

    return (
        <FormProvider {...methods}>
            <form id="ingredient-form" onSubmit={handleSubmit(onSubmit)}>
                <div className="mx-auto max-w-4xl px-4 py-8">
                    <div className="overflow-hidden rounded-xl border-2 border-t-red-600 bg-white shadow-sm">
                        <div className="border-b border-gray-100 px-6 py-4">
                            <div className="flex items-center justify-between">
                                <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-800">
                                    <Package className="h-5 w-5 text-red-500" />
                                    اطلاعات ماده اولیه
                                </h2>
                                <button
                                    type="submit"
                                    form="ingredient-form"
                                    className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <Save className="ml-1 inline h-4 w-4" />
                                    ذخیره
                                </button>
                            </div>
                        </div>

                        <div className="space-y-6 p-6">
                            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                                <FormInput name="name" label="نام ماده *" placeholder="مثلاً تخم‌مرغ، آرد، شکر" />
                                <FormInput
                                    name="reorderLevel"
                                    label="مقدار"
                                    type="number"
                                    placeholder="مقدار موجودی"
                                />
                                <FormSelect
                                    name="unit"
                                    label="واحد *"
                                    options={Object.entries(Unit).map(([value]) => ({
                                        value,
                                        label: '',
                                    }))}
                                />
                            </div>

                            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                                <FormInput
                                    name="reorderLevel"
                                    label="سطح هشدار موجودی"
                                    type="number"
                                    placeholder="حداقل مجاز"
                                />
                                <FormInput
                                    name="reorderQuantity"
                                    label="مقدار پیشنهادی خرید"
                                    type="number"
                                    placeholder="مقدار سفارش مجدد"
                                />
                                <FormInput
                                    name="costPrice"
                                    label="قیمت تمام‌شده (تومان)"
                                    type="number"
                                />
                            </div>

                            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                                <FormInput name="categoryId" label="دسته‌بندی" placeholder="پروتئین،سبزیجات" />
                                <FormSwitch name="complete" label="وضعیت ماده" description="آماده / نیمه‌آماده" />

                            </div>

                        </div>
                    </div>
                </div>
            </form>
        </FormProvider>
    );
};