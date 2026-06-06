// src/presentation/pages/CreateMenuPage.tsx
import { zodResolver } from '@hookform/resolvers/zod';
import { FormProvider, useForm, useFieldArray } from 'react-hook-form';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreateMenuWithItems } from '../hooks/useCreateMenuWithItems';
import { useNavbar } from '../hooks/useNavbar';
import { FormInput } from '../components/form/FormInput';
import { FormTextarea } from '../components/form/FormTextarea';
import {Save, Menu as MenuIcon, Plus, Trash2, ArrowBigLeft} from 'lucide-react';
import {
    type CreateMenuWithItemsInput,
    CreateMenuWithItemsSchema
} from "../../domain/use-cases/product/menu/CreateMenuWithItems.ts";
import {FormFile} from "../components/form/FormFile.tsx";

export const CreateMenuPage = () => {
    const navigate = useNavigate();
    const {setRightElement, setShowMenu } = useNavbar();
    const { mutate: createMenu } = useCreateMenuWithItems();

    const methods = useForm<CreateMenuWithItemsInput>({
        resolver: zodResolver(CreateMenuWithItemsSchema),
        defaultValues: {
            name: '',
            category: '',
            description: null,
            sortOrder: 0,
            isActive: true,
            items: [
                {
                    name: '',
                    description: null,
                    price: 0,
                    imageUrl: null,
                    isAvailable: true,
                    recipeId: '',
                },
            ],
        },
    });

    const { fields, append, remove } = useFieldArray({
        control: methods.control,
        name: 'items',
    });

    useEffect(() => {
        setShowMenu(false);
        setRightElement(
            <button
                type="submit"
                form="menu-form"
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

    const onSubmit = (data: CreateMenuWithItemsInput) => {
        createMenu(data, {
            onSuccess: () => navigate('/menus'),
        });
    };

    return (
        <FormProvider {...methods}>
            <form id="menu-form" onSubmit={methods.handleSubmit(onSubmit)}>
                <div className="mx-auto max-w-5xl px-4 py-8">
                    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                        {/* هدر کارت */}
                        <div className="border-b border-gray-100 px-6 py-4">
                            <div className="flex items-center justify-between">
                                <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-800">
                                    <MenuIcon className="h-5 w-5 text-red-500" />
                                    اطلاعات منو
                                </h2>
                                <button
                                    type="submit"
                                    form="menu-form"
                                    className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
                                >
                                    <Save className="ml-1 inline h-4 w-4" />
                                    ذخیره منو
                                </button>
                            </div>
                        </div>

                        <div className="space-y-8 p-6">
                            {/* اطلاعات منو */}
                            <section>
                                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                                    <FormInput name="menu.name" label="نام منو *" />
                                    <FormInput name="menu.category" label="دسته‌بندی *" />
                                    <FormTextarea name="menu.description" label="توضیحات" rows={2} />
                                    <FormInput name="menu.sortOrder" label="ترتیب نمایش" type="number" />
                                </div>
                            </section>

                            {/* آیتم‌های منو */}
                            <section>
                                <div className="mb-4 flex items-center justify-between border-b border-gray-200 pb-2">
                                    <div className="flex items-center gap-2">
                                        <MenuIcon className="h-5 w-5 text-emerald-500" />
                                        <h3 className="text-base font-semibold text-gray-800">آیتم‌های منو</h3>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() =>
                                            append({
                                                name: '',
                                                description: null,
                                                price: 0,
                                                imageUrl: null,
                                                isAvailable: true,
                                                recipeId: '',
                                            })
                                        }
                                        className="flex items-center gap-1 rounded-lg bg-emerald-50 px-3 py-1.5 text-sm text-emerald-600 hover:bg-emerald-100"
                                    >
                                        <Plus className="h-4 w-4" />
                                        افزودن آیتم
                                    </button>
                                </div>

                                <div className="space-y-4">
                                    {fields.map((field, index) => (
                                        <div key={field.id} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                                            <div className="mb-3 flex items-center justify-between">
                                                <span className="text-sm font-medium text-gray-500">آیتم {index + 1}</span>
                                                <button
                                                    type="button"
                                                    onClick={() => remove(index)}
                                                    className="text-red-400 hover:text-red-600"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </button>
                                            </div>
                                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                                <FormInput name={`items.${index}.name`} label="نام آیتم *" />
                                                <FormInput name={`items.${index}.price`} label="قیمت (تومان) *" type="number" />
                                                <FormTextarea name={`items.${index}.description`} label="توضیحات" rows={2} />
                                                <FormFile name={`items.${index}.imageFile`} label="تصویر" />
                                                <FormInput name={`items.${index}.recipeId`} label="رسپی" />
                                            </div>
                                        </div>
                                    ))}

                                    {fields.length === 0 && (
                                        <div className="rounded-lg border-2 border-dashed border-gray-200 py-8 text-center text-sm text-gray-400">
                                            برای افزودن آیتم، دکمه «افزودن آیتم» را بزنید
                                        </div>
                                    )}
                                </div>
                            </section>
                        </div>
                    </div>
                </div>
            </form>
        </FormProvider>
    );
};