// src/presentation/pages/CreatePurchaseOrderPage.tsx
import { zodResolver } from '@hookform/resolvers/zod';
import { FormProvider, useForm } from 'react-hook-form';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCreatePurchaseOrder } from '../hooks/useCreatePurchaseOrder';
import { useNavbar } from '../hooks/useNavbar';
import { FormInput } from '../components/form/FormInput';
import { PurchaseOrderItemList } from '../components/form/PurchaseOrderItemList';
import {Save, FileText, Package, ArrowBigLeft} from 'lucide-react';
import {
    type CreatePurchaseOrderWithItemsInput,
    CreatePurchaseOrderWithItemsSchema
} from "../../domain/use-cases/inventory/facture/CreatePurchaseOrderWithItems.ts";
import {FormTextarea} from "../components/form/FormTextarea.tsx";

export const CreatePurchaseOrderPage = () => {
    const navigate = useNavigate();
    const {setRightElement, setShowMenu } = useNavbar();
    const { mutate: createOrder} = useCreatePurchaseOrder();

    const methods = useForm({
        resolver: zodResolver(CreatePurchaseOrderWithItemsSchema),
        defaultValues: {
            supplierId: '',
            expectedDeliveryDate: null,
            invoiceNumber: null,
            notes: null,
            items: [],
        },
    });

    useEffect(() => {
        setShowMenu(false);
        setRightElement(
            <button
                type="submit"
                form="purchase-order-form"
                className="rounded-lg bg-red-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-red-700"
            >
                <ArrowBigLeft className="ml-1 inline h-4 w-4" />
                بازگشت
            </button>
        );
        return () => {
            setShowMenu(true);
            setRightElement(null);
        };
    }, [setRightElement, setShowMenu]);

    const onSubmit = (data: CreatePurchaseOrderWithItemsInput) => {
        createOrder(data, {
            onSuccess: () => navigate('/purchase-orders'),
        });
    };

    return (
        <FormProvider {...methods}>
            <form id="purchase-order-form" onSubmit={methods.handleSubmit(onSubmit)}>
                <div className="mx-auto max-w-5xl px-4 py-8">
                    <div className="overflow-hidden rounded-xl border-2 border-t-red-600 bg-white shadow-sm">
                        <div className="border-b border-gray-100 px-6 py-4">
                            <div className="flex items-center justify-between">
                                <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-800">
                                    <FileText className="h-5 w-5 text-red-500" />
                                    اطلاعات فاکتور خرید
                                </h2>
                                <button
                                    type="submit"
                                    form="purchase-order-form"
                                    className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
                                >
                                    <Save className="ml-1 inline h-4 w-4" />
                                    ثبت فاکتور
                                </button>
                            </div>
                        </div>

                        <div className="space-y-8 p-6">
                            {/* اطلاعات سر فاکتور */}
                            <section>
                                <div className="mb-4 flex items-center gap-2 border-b border-gray-200 pb-2">
                                    <FileText className="h-5 w-5 text-red-500" />
                                    <h3 className="text-base font-semibold text-gray-800">اطلاعات اصلی</h3>
                                </div>
                                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                                    <FormInput name="name" label="نام تأمین‌کننده *" />
                                    <FormInput name="expectedDeliveryDate" label="تاریخ خرید" type="date" />
                                </div>

                                <div className="grid grid-cols-1 gap-5 md:grid-cols-1 mt-6">
                                    <FormTextarea name="description" label="توضیحات" rows={3} />
                                </div>
                            </section>

                            {/* آیتم‌های خرید */}
                            <section>
                                <div className="mb-4 flex items-center gap-2 border-b border-gray-200 pb-2">
                                    <Package className="h-5 w-5 text-emerald-500" />
                                    <h3 className="text-base font-semibold text-gray-800">اقلام خرید</h3>
                                </div>
                                <PurchaseOrderItemList />
                            </section>
                        </div>
                    </div>
                </div>
            </form>
        </FormProvider>
    );
};