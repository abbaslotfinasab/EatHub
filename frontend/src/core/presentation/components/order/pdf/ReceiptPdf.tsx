import type {OrderWithItems} from "../../../../domain/entities/product/order/OrderWithItems";

import {formatCurrency} from "../../../utils/formatCurrency";
import {formatDateTime} from "../../../utils/formatDateTime";

import "./ReceiptPdf.css";


/* ================================================================
   Props
================================================================ */


interface ReceiptPdfProps {

    /**
     * HTML element id used by usePrintReceipt.
     */
    id?: string;

    /**
     * Order data.
     */
    order: OrderWithItems;

}


/* ================================================================
   Main Component
================================================================ */


export function ReceiptPdf({
    id = "receipt-pdf",
    order,
}: ReceiptPdfProps) {

    const data = order.order;


    return (
        <article
            id={id}
            className="receipt-pdf"
            dir="rtl"
        >

            {/* =====================================================
                Header
            ===================================================== */}

            <header className="receipt-pdf__header">

                <div className="receipt-pdf__business">

                    <div className="receipt-pdf__business-name">
                        {data.businessName ?? "رستوران"}
                    </div>

                    <div className="receipt-pdf__document-title">
                        رسید سفارش
                    </div>

                </div>


                <div className="receipt-pdf__meta">

                    <div className="receipt-pdf__meta-row">

                        <span>
                            شماره سفارش
                        </span>

                        <strong>
                            #{data.id}
                        </strong>

                    </div>


                    <div className="receipt-pdf__meta-row">

                        <span>
                            تاریخ
                        </span>

                        <strong>
                            {data.createdAt
                                ? formatDateTime(data.createdAt)
                                : "-"}
                        </strong>

                    </div>

                </div>

            </header>


            <Divider/>


            {/* =====================================================
                Customer / Order Information
            ===================================================== */}

            <section className="receipt-pdf__information">

                <SectionTitle>
                    اطلاعات سفارش
                </SectionTitle>


                <div className="receipt-pdf__information-grid">

                    <InfoField
                        label="مشتری"
                        value={
                            data.customerName ??
                            "مشتری عمومی"
                        }
                    />


                    {data.customerPhone && (
                        <InfoField
                            label="تلفن"
                            value={data.customerPhone}
                        />
                    )}


                    <InfoField
                        label="نوع سفارش"
                        value={getOrderTypeLabel(
                            data.orderType,
                        )}
                    />


                    {data.tableId && (
                        <InfoField
                            label="میز"
                            value={String(data.tableId)}
                        />
                    )}


                    <InfoField
                        label="وضعیت پرداخت"
                        value={getPaymentStatusLabel(
                            data.paymentStatus,
                        )}
                    />


                    {data.paymentMethod && (
                        <InfoField
                            label="روش پرداخت"
                            value={getPaymentMethodLabel(
                                data.paymentMethod,
                            )}
                        />
                    )}

                </div>

            </section>


            <Divider/>


            {/* =====================================================
                Items
            ===================================================== */}

            <section className="receipt-pdf__items">

                <SectionTitle>
                    اقلام سفارش
                </SectionTitle>


                <table className="receipt-pdf__items-table">

                    <thead>

                        <tr>

                            <th className="receipt-pdf__col-number">
                                #
                            </th>

                            <th className="receipt-pdf__col-product">
                                محصول
                            </th>

                            <th className="receipt-pdf__col-quantity">
                                تعداد
                            </th>

                            <th className="receipt-pdf__col-price">
                                قیمت واحد
                            </th>

                            <th className="receipt-pdf__col-total">
                                مبلغ
                            </th>

                        </tr>

                    </thead>


                    <tbody>

                        {order.orderItems.map(
                            (item, index) => (

                                <tr key={item.id}>

                                    <td className="receipt-pdf__col-number">
                                        {index + 1}
                                    </td>


                                    <td className="receipt-pdf__product">

                                        <div className="receipt-pdf__product-name">
                                            {item.menuItemName}
                                        </div>


                                        {item.notes && (
                                            <div className="receipt-pdf__product-note">
                                                {item.notes}
                                            </div>
                                        )}

                                    </td>


                                    <td className="receipt-pdf__col-quantity">
                                        {item.quantity}
                                    </td>


                                    <td className="receipt-pdf__col-price">
                                        {formatCurrency(
                                            item.unitPrice,
                                        )}
                                    </td>


                                    <td className="receipt-pdf__col-total">
                                        {formatCurrency(
                                            item.totalPrice,
                                        )}
                                    </td>

                                </tr>

                            ),
                        )}

                    </tbody>

                </table>

            </section>


            <Divider/>


            {/* =====================================================
                Financial Summary
            ===================================================== */}

            <section className="receipt-pdf__financial">

                <div className="receipt-pdf__financial-content">

                    <div className="receipt-pdf__financial-rows">

                        <SummaryRow
                            label="جمع سفارش"
                            value={formatCurrency(
                                data.subtotal,
                            )}
                        />


                        {Number(data.discount) > 0 && (
                            <SummaryRow
                                label="تخفیف"
                                value={formatCurrency(
                                    data.discount,
                                )}
                            />
                        )}


                        {Number(data.tax) > 0 && (
                            <SummaryRow
                                label="مالیات"
                                value={formatCurrency(
                                    data.tax,
                                )}
                            />
                        )}

                    </div>


                    <div className="receipt-pdf__grand-total">

                        <span>
                            مبلغ قابل پرداخت
                        </span>

                        <strong>
                            {formatCurrency(
                                data.totalAmount,
                            )}
                        </strong>

                    </div>

                </div>

            </section>


            {/* =====================================================
                Payment
            ===================================================== */}

            <section className="receipt-pdf__payment">

                <SectionTitle>
                    پرداخت
                </SectionTitle>


                <div className="receipt-pdf__payment-box">

                    <InfoField
                        label="وضعیت"
                        value={getPaymentStatusLabel(
                            data.paymentStatus,
                        )}
                    />


                    {data.paymentMethod && (
                        <InfoField
                            label="روش پرداخت"
                            value={getPaymentMethodLabel(
                                data.paymentMethod,
                            )}
                        />
                    )}

                </div>

            </section>


            {/* =====================================================
                Notes
            ===================================================== */}

            {data.notes && (

                <section className="receipt-pdf__notes">

                    <Divider/>

                    <SectionTitle>
                        توضیحات
                    </SectionTitle>


                    <div className="receipt-pdf__notes-content">
                        {data.notes}
                    </div>

                </section>

            )}


            {/* =====================================================
                Footer
            ===================================================== */}

            <footer className="receipt-pdf__footer">

                <div className="receipt-pdf__footer-title">
                    از خرید شما سپاسگزاریم
                </div>


                <div className="receipt-pdf__footer-subtitle">
                    سفارش شما با موفقیت ثبت شد
                </div>


                <div className="receipt-pdf__footer-generated">
                    این رسید به صورت الکترونیکی صادر شده است.
                </div>

            </footer>

        </article>
    );
}


/* ================================================================
   Divider
================================================================ */


function Divider() {

    return (
        <div
            className="receipt-pdf__divider"
            aria-hidden="true"
        />
    );
}


/* ================================================================
   Section Title
================================================================ */


interface SectionTitleProps {

    children: React.ReactNode;

}


function SectionTitle({
    children,
}: SectionTitleProps) {

    return (
        <h2 className="receipt-pdf__section-title">
            {children}
        </h2>
    );
}


/* ================================================================
   Info Field
================================================================ */


interface InfoFieldProps {

    label: string;

    value: React.ReactNode;

}


function InfoField({
    label,
    value,
}: InfoFieldProps) {

    return (
        <div className="receipt-pdf__info-field">

            <span className="receipt-pdf__info-label">
                {label}
            </span>


            <span className="receipt-pdf__info-value">
                {value}
            </span>

        </div>
    );
}


/* ================================================================
   Summary Row
================================================================ */


interface SummaryRowProps {

    label: string;

    value: React.ReactNode;

}


function SummaryRow({
    label,
    value,
}: SummaryRowProps) {

    return (
        <div className="receipt-pdf__summary-row">

            <span>
                {label}
            </span>

            <strong>
                {value}
            </strong>

        </div>
    );
}


/* ================================================================
   Labels
================================================================ */


/**
 * Order type label.
 */
function getOrderTypeLabel(
    type: string,
): string {

    switch (type) {

        case "dine_in":
            return "حضوری";

        case "takeaway":
            return "بیرون‌بر";

        case "delivery":
            return "ارسال";

        default:
            return type;

    }
}


/**
 * Payment status label.
 */
function getPaymentStatusLabel(
    status?: string,
): string {

    switch (status) {

        case "paid":
            return "پرداخت شده";

        case "unpaid":
            return "پرداخت نشده";

        case "pending":
            return "در انتظار پرداخت";

        case "failed":
            return "پرداخت ناموفق";

        case "refunded":
            return "مسترد شده";

        default:
            return "-";

    }
}


/**
 * Payment method label.
 */
function getPaymentMethodLabel(
    method: string,
): string {

    switch (method) {

        case "cash":
            return "نقدی";

        case "card":
            return "کارت بانکی";

        case "customer_account":
            return "حساب مشتری";

        default:
            return method;

    }
}