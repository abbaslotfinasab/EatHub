// src/presentation/pages/CreateRecipePage.tsx
import { zodResolver } from '@hookform/resolvers/zod';
import { FormProvider, useForm } from 'react-hook-form';
import { useCreateRecipe } from '../hooks/useCreateRecipe';
import { FormInput } from '../components/form/FormInput';
import { IngredientList } from '../components/form/IngredientList';
import { FormTextarea } from '../components/form/FormTextarea';
import {Save, Package, ArrowBigLeft} from 'lucide-react';
import { useEffect } from 'react';
import { useNavbar } from '../hooks/useNavbar';
import {
    type CreateRecipeInput,
    CreateRecipeSchema
} from "../../domain/use-cases/product/recipe/CreateRecipeWithComponents";

export const CreateRecipePage = () => {
    const methods = useForm<CreateRecipeInput>({
        resolver: zodResolver(CreateRecipeSchema),
        defaultValues: {
            name: '',
            description: '',
            ingredients: [],
        },
    });

    const { mutate: createRecipe } = useCreateRecipe();
    const {setRightElement, setShowMenu } = useNavbar();

    // تنظیم Navbar برای این صفحه
    useEffect(() => {
        setShowMenu(false); // منوی نوار را مخفی می‌کنیم (فقط لوگو و دکمه راست دیده می‌شود)
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
            setShowMenu(false);

        };
    }, [setRightElement, setShowMenu]);

    const onSubmit = (data: CreateRecipeInput) => createRecipe(data);

    return (
        <FormProvider {...methods}>
            <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 py-8">
                <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">

                    {/* کارت اصلی */}
                    <div className="overflow-hidden rounded-xl border-2 border-t-rose-600 bg-white shadow-md">
                        <form id="recipe-form" onSubmit={methods.handleSubmit(onSubmit)} className="p-5 sm:p-6">
                            <div className="space-y-8">
                                {/* بخش اطلاعات پایه */}
                                <section>
                                    <div className="flex items-center justify-between border-b pb-3">
                                        <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-800">
                                            <Package className="h-5 w-5 text-red-500" />
                                            اطلاعات پایه
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
                                    <div className="grid grid-cols-1 gap-5 md:grid-cols-2 mt-6">
                                        <FormInput name="name" label="نام رسپی *" />
                                        <FormTextarea name="description" label="توضیحات" rows={3} />
                                    </div>
                                </section>

                                {/* بخش مواد مصرفی */}
                                <section>
                                    <div className="mb-4 flex items-center gap-2 border-b border-gray-200 pb-2">
                                        <Package className="h-5 w-5 text-emerald-500" />
                                        <h2 className="text-lg font-semibold text-gray-800">
                                            مواد مصرفی
                                        </h2>
                                    </div>
                                    <IngredientList />
                                </section>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </FormProvider>
    );
};