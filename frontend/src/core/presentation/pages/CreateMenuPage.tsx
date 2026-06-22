// src/presentation/pages/CreateMenuPage.tsx
import {zodResolver} from '@hookform/resolvers/zod';
import {FormProvider, useForm, useFieldArray} from 'react-hook-form';
import {useEffect} from 'react';
import {useNavigate} from 'react-router-dom';
import {useCreateMenuWithItems} from '../hooks/useCreateMenuWithItems';
import {useNavbar} from '../hooks/useNavbar';
import {FormInput} from '../components/form/FormInput';
import {FormTextarea} from '../components/form/FormTextarea';
import {Save, Menu as MenuIcon, Plus, Trash2} from 'lucide-react';
import {
    type CreateMenuWithItemsInput,
    CreateMenuWithItemsSchema
} from "../../domain/use-cases/product/menu/CreateMenuWithItems.ts";
import {FormFile} from "../components/form/FormFile.tsx";

export const CreateMenuPage = () => {
    const navigate = useNavigate();
    const {setRightElement, setShowMenu} = useNavbar();
    const {mutate: createMenu} = useCreateMenuWithItems();

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
                imageFile: null,
                isAvailable: true,
                recipeId: '',
            },
        ],
    },
});

    const {fields, append, remove} = useFieldArray({
        control: methods.control,
        name: 'items',
    });

    useEffect(() => {
        setShowMenu(false);
        return () => {
            setShowMenu(true);
            setRightElement(null);
        };
    }, [setRightElement, setShowMenu]);


    return (
        <FormProvider {...methods}>
            <form id="menu-form"onSubmit={methods.handleSubmit(
        (data) => {
            console.log("SUBMIT SUCCESS", data);

            createMenu(data, {
                onSuccess: () => {
                    navigate('/menus');
                },
            });
        },
        (errors) => {
            console.log("SUBMIT ERRORS", errors);
        }
    )}>
                <div className="mx-auto max-w-5xl px-4 py-8">

                    <div className="overflow-hidden rounded-2xl border border-[#e5e7eb] bg-white shadow-sm">

                        {/* HEADER */}
                        <div className="border-b border-gray-100 bg-[#10281A] px-6 py-5">
                            <div className="flex items-center justify-between">

                                <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
                                    <MenuIcon className="h-5 w-5 text-white/80"/>
                                    اطلاعات منو
                                </h2>

                                <button
                                    type="submit"
                                    form="menu-form"
                                    className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-[#10281A] hover:bg-gray-100 transition"
                                >
                                    <Save className="ml-1 inline h-4 w-4"/>
                                    ذخیره منو
                                </button>

                            </div>
                        </div>

                        {/* BODY */}
                        <div className="space-y-8 p-6">

                            {/* MENU INFO */}
                            <section>
                                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">

                                    <FormInput name="name" label="نام منو *"/>
                                    <FormInput name="category" label="دسته‌بندی *"/>
                                    <FormTextarea name="description" label="توضیحات" rows={2}/>
                                    <FormInput name="sortOrder" label="ترتیب نمایش" type="number"/>
                                </div>
                            </section>

                            {/* ITEMS HEADER */}
                            <section>
                                <div className="mb-4 flex items-center justify-between border-b border-gray-200 pb-3">

                                    <div className="flex items-center gap-2">
                                        <MenuIcon className="h-5 w-5 text-[#10281A]"/>
                                        <h3 className="text-base font-semibold text-gray-800">
                                            آیتم‌های منو
                                        </h3>
                                    </div>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            append({
                                                name: "",
                                                description: null,
                                                price: 0,
                                                imageFile: null,
                                                isAvailable: true,
                                                recipeId: "",
                                            })
                                        }
                                        className="flex items-center gap-1 rounded-lg bg-[#10281A]/10 px-3 py-1.5 text-sm text-[#10281A] hover:bg-[#10281A]/20 transition"
                                    >
                                        <Plus className="h-4 w-4"/>
                                        افزودن آیتم
                                    </button>

                                </div>

                                {/* ITEMS */}
                                <div className="space-y-4">

                                    {fields.map((field, index) => (
                                        <div
                                            key={field.id}
                                            className="rounded-xl border border-gray-200 bg-gray-50 p-4 hover:shadow-sm transition"
                                        >

                                            <div className="mb-3 flex items-center justify-between">
                                            <span className="text-sm font-medium text-gray-500">
                                                آیتم {index + 1}
                                            </span>

                                                <button
                                                    type="button"
                                                    onClick={() => remove(index)}
                                                    className="text-gray-400 hover:text-red-500 transition"
                                                >
                                                    <Trash2 className="h-4 w-4"/>
                                                </button>
                                            </div>

                                            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">

                                                <FormInput name={`items.${index}.name`} label="نام آیتم *"/>
                                                <FormInput name={`items.${index}.price`} label="قیمت (تومان) *"
                                                           type="number"/>
                                                <FormTextarea name={`items.${index}.description`} label="توضیحات"
                                                              rows={2}/>
                                                <FormFile name={`items.${index}.imageFile`} label="تصویر"/>
                                                <FormInput name={`items.${index}.recipeId`} label="رسپی"/>

                                            </div>
                                        </div>
                                    ))}

                                    {fields.length === 0 && (
                                        <div
                                            className="rounded-xl border-2 border-dashed border-gray-200 py-10 text-center text-sm text-gray-400">
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