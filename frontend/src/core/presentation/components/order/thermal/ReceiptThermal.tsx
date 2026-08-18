import type {OrderWithItems} from "../../../../domain/entities/product/order/OrderWithItems";

import {formatCurrency} from "../../../utils/formatCurrency";
import {formatDateTime} from "../../../utils/formatDateTime";

import "./ReceiptThermal.css";


interface ReceiptThermalProps {

    /**
     * HTML element id used by usePrintReceipt.
     */
    id?: string;

    /**
     * Order data.
     */
    order: OrderWithItems;

    /**
     * Thermal printer paper width.
     */
    paper?: 58 | 80;

}


export function ReceiptThermal({
    id,
    order,
    paper = 80,
}: ReceiptThermalProps) {

    const data = order.order;

    const is58mm = paper === 58;


    return (
        <div
            id={id}
            dir="rtl"
            className={[
                "thermal-receipt",
                is58mm
                    ? "thermal-receipt--58"
                    : "thermal-receipt--80",
            ].join(" ")}
        >

            {/* =====================================================
                Header
            ===================================================== */}

            <header className="thermal-receipt__header">

                <div className="thermal-receipt__business-name">
                    {data.businessName ?? "رستوران"}
                </div>

                <div className="thermal-receipt__title">
                    رسید سفارش
                </div>

                <div className="thermal-receipt__order-number">
                    شماره سفارش: #{data.id}
                </div>

            </header>


            <ThermalDivider/>


            {/* =====================================================
                Order Information
            ===================================================== */}

            <section className="thermal-receipt__info">

                <InfoRow
                    label="تاریخ"
                    value={
                        data.createdAt
                            ? formatDateTime(data.createdAt)
                            : "-"
                    }
                />

                <InfoRow
                    label="مشتری"
                    value={
                        data.customerName ??
                        "مشتری عمومی"
                    }
                />

                {data.customerPhone && (
                    <InfoRow
                        label="تلفن"
                        value={data.customerPhone}
                    />
                )}

                <InfoRow
                    label="نوع سفارش"
                    value={getOrderTypeLabel(data.orderType)}
                />

                {data.tableId && (
                    <InfoRow
                        label="میز"
                        value={String(data.tableId)}
                    />
                )}

            </section>


            <ThermalDivider/>


            {/* =====================================================
                Items
            ===================================================== */}

            <section className="thermal-receipt__items">

                <div
                    className={[
                        "thermal-receipt__items-header",
                        is58mm
                            ? "thermal-receipt__items-header--58"
                            : "thermal-receipt__items-header--80",
                    ].join(" ")}
                >

                    <div>
                        کالا / محصول
                    </div>


                    {!is58mm && (
                        <div className="thermal-receipt__quantity-header">
                            تعداد
                        </div>
                    )}


                    <div className="thermal-receipt__price-header">
                        مبلغ
                    </div>

                </div>


                <div className="thermal-receipt__items-list">

                    {order.orderItems.map((item) => (

                        <ThermalItem
                            key={item.id}
                            item={item}
                            paper={paper}
                        />

                    ))}

                </div>

            </section>


            <ThermalDivider/>


            {/* =====================================================
                Summary
            ===================================================== */}

            <section className="thermal-receipt__summary">

                <SummaryRow
                    label="جمع سفارش"
                    value={formatCurrency(data.subtotal)}
                />


                {Number(data.discount) > 0 && (
                    <SummaryRow
                        label="تخفیف"
                        value={formatCurrency(data.discount)}
                    />
                )}


                {Number(data.tax) > 0 && (
                    <SummaryRow
                        label="مالیات"
                        value={formatCurrency(data.tax)}
                    />
                )}

            </section>


            <ThermalDivider/>


            {/* =====================================================
                Total
            ===================================================== */}

            <section className="thermal-receipt__total">

                <span className="thermal-receipt__total-label">
                    مبلغ قابل پرداخت
                </span>

                <span className="thermal-receipt__total-value">
                    {formatCurrency(data.totalAmount)}
                </span>

            </section>


            <ThermalDivider/>


            {/* =====================================================
                Payment
            ===================================================== */}

            <section className="thermal-receipt__payment">

                <InfoRow
                    label="وضعیت پرداخت"
                    value={getPaymentStatusLabel(
                        data.paymentStatus,
                    )}
                />


                {data.paymentMethod && (
                    <InfoRow
                        label="روش پرداخت"
                        value={getPaymentMethodLabel(
                            data.paymentMethod,
                        )}
                    />
                )}

            </section>


            {/* =====================================================
                Notes
            ===================================================== */}

            {data.notes && (
                <>
                    <ThermalDivider/>

                    <section className="thermal-receipt__notes">

                        <div className="thermal-receipt__notes-title">
                            توضیحات
                        </div>

                        <div className="thermal-receipt__notes-text">
                            {data.notes}
                        </div>

                    </section>
                </>
            )}


            <ThermalDivider/>


            {/* =====================================================
                Footer
            ===================================================== */}

            <footer className="thermal-receipt__footer">

                <div className="thermal-receipt__footer-title">
                    از خرید شما سپاسگزاریم
                </div>

                <div className="thermal-receipt__footer-subtitle">
                    سفارش شما با موفقیت ثبت شد
                </div>

            </footer>

        </div>
    );
}


/* ================================================================
   Item
================================================================ */


interface ThermalItemProps {

    item: OrderWithItems["orderItems"][number];

    paper: 58 | 80;

}


function ThermalItem({
    item,
    paper,
}: ThermalItemProps) {

    const is58mm = paper === 58;


    if (is58mm) {

        return (
            <article className="thermal-receipt__item thermal-receipt__item--58">

                <div className="thermal-receipt__item-name">
                    {item.menuItemName}
                </div>


                <div className="thermal-receipt__item-meta">

                    <span>
                        {item.quantity}
                        {" × "}
                        {formatCurrency(item.unitPrice)}
                    </span>


                    <strong>
                        {formatCurrency(item.totalPrice)}
                    </strong>

                </div>


                {item.notes && (
                    <div className="thermal-receipt__item-notes">
                        {item.notes}
                    </div>
                )}

            </article>
        );
    }


    return (
        <article className="thermal-receipt__item thermal-receipt__item--80">

            <div className="thermal-receipt__item-product">

                <div className="thermal-receipt__item-name">
                    {item.menuItemName}
                </div>


                {item.notes && (
                    <div className="thermal-receipt__item-notes">
                        {item.notes}
                    </div>
                )}

            </div>


            <div className="thermal-receipt__item-quantity">
                {item.quantity}
            </div>


            <div className="thermal-receipt__item-price">
                {formatCurrency(item.totalPrice)}
            </div>

        </article>
    );
}


/* ================================================================
   Divider
================================================================ */


function ThermalDivider() {

    return (
        <div
            className="thermal-receipt__divider"
            aria-hidden="true"
        />
    );
}


/* ================================================================
   Info Row
================================================================ */


interface InfoRowProps {

    label: string;

    value: React.ReactNode;

}


function InfoRow({
    label,
    value,
}: InfoRowProps) {

    return (
        <div className="thermal-receipt__info-row">

            <span className="thermal-receipt__info-label">
                {label}
            </span>


            <span className="thermal-receipt__info-value">
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
        <div className="thermal-receipt__summary-row">

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