import {useEffect, useState} from "react";
import {isAxiosError} from "axios";
import {Alert, CircularProgress, Divider, Stack, TextField, Typography} from "@mui/material";
import {LoadingButton} from "@mui/lab";
import type {UseQueryResult} from "@tanstack/react-query";

import {useRecordOrderConsumption} from "../../hooks/order/useRecordOrderConsumption.ts";
import type {OrderConsumptionRequirements} from "../../../domain/entities/product/order/OrderInventoryConsumption.ts";
import {useAuthStore} from "../../store/auth.store.ts";
import {
    clearPendingOrderConsumption,
    createPendingOrderConsumptionRequest,
    readPendingOrderConsumption,
    savePendingOrderConsumption,
    type PendingOrderConsumptionRequest,
} from "../../utils/orderConsumptionRequestIdentity.ts";

interface Props {
    orderId: string;
    requirementsQuery: UseQueryResult<OrderConsumptionRequirements, Error>;
}

const unitLabels: Record<string, string> = {
    kg: "کیلوگرم",
    g: "گرم",
    l: "لیتر",
    ml: "میلی‌لیتر",
    pc: "عدد",
    pk: "بسته",
};

function displayUnit(unit: string): string {
    return unitLabels[unit] ?? unit;
}

function collectMessages(value: unknown): string[] {
    if (typeof value === "string") return [value];
    if (Array.isArray(value)) return value.flatMap(collectMessages);
    if (value && typeof value === "object") {
        return Object.values(value as Record<string, unknown>).flatMap(collectMessages);
    }
    return [];
}

function errorMessage(error: unknown): string {
    if (isAxiosError(error)) {
        const messages = collectMessages(error.response?.data);
        if (messages.length) return messages.join(" ");
    }
    return "ثبت مصرف واقعی انجام نشد. مقادیر و دسترسی خود را بررسی کنید.";
}

function validQuantity(value: string): boolean {
    const trimmed = value.trim();
    if (!/^(?:\d+(?:\.\d*)?|\.\d+)$/.test(trimmed)) return false;
    const [whole, fraction = ""] = trimmed.split(".");
    const integer = whole || "0";
    return integer.length <= 24 && fraction.length <= 12;
}

export function OrderActualConsumptionPanel({orderId, requirementsQuery}: Props) {
    const recordMutation = useRecordOrderConsumption();
    const [quantities, setQuantities] = useState<Record<number, string>>({});
    const [validationError, setValidationError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    useEffect(() => {
        if (businessId === null) return;
        try {
            const restored = readPendingOrderConsumption(
                String(businessId),
                orderId,
                window.sessionStorage,
            );
            if (restored) {
                setPendingRequest(restored);
                setQuantities(Object.fromEntries(
                    restored.lines.map((line) => [line.requirementId, line.quantity]),
                ));
            } else {
                setPendingRequest(null);
            }
            setStorageError(null);
        } catch {
            setStorageError("بازیابی درخواست قبلی امن نبود؛ برای جلوگیری از ثبت مصرف تکراری، درخواست جدید ارسال نمی‌شود.");
        }
    }, [businessId, orderId]);

    const requirements = requirementsQuery.data?.requirements ?? [];
    const submit = async () => {
        setValidationError(null);
        setSuccess(false);
        const missing = requirements.some((line) => !(quantities[line.requirementId] ?? "").trim());
        if (missing) {
            setValidationError("برای هر ماده، مقدار مصرف واقعی این ثبت را وارد کنید؛ در صورت عدم مصرف، صفر بنویسید.");
            return;
        }
        if (requirements.some((line) => !validQuantity(quantities[line.requirementId] ?? ""))) {
            setValidationError("مقدار باید عددی نامنفی و حداکثر با ۱۲ رقم اعشار باشد.");
            return;
        }

        if (businessId === null) {
            setStorageError("کسب‌وکار فعال مشخص نیست؛ درخواست مصرف ارسال نشد.");
            return;
        }

        if (storageError) {
            setValidationError(storageError);
            return;
        }

        let request = pendingRequest;
        if (!request) {
            const lines = requirements.map((line) => ({
                requirementId: line.requirementId,
                quantity: quantities[line.requirementId].trim(),
                unit: line.unit,
            }));
            try {
                request = createPendingOrderConsumptionRequest(
                    String(businessId),
                    orderId,
                    lines,
                    crypto.randomUUID(),
                );
                savePendingOrderConsumption(request, window.sessionStorage);
                setPendingRequest(request);
            } catch {
                setStorageError("ذخیره شناسه امن درخواست ناموفق بود؛ برای جلوگیری از ثبت مصرف تکراری، درخواست ارسال نشد.");
                return;
            }
        }

        try {
            await recordMutation.mutateAsync({
                orderId,
                idempotencyKey: request.key,
                lines: request.lines,
            });
            try {
                clearPendingOrderConsumption(String(businessId), orderId, window.sessionStorage);
                setPendingRequest(null);
                setStorageError(null);
                setQuantities({});
                setSuccess(true);
            } catch {
                setValidationError("مصرف ثبت شد، اما پاک‌سازی شناسه محلی انجام نشد؛ در صورت نیاز فقط همان درخواست را دوباره ارسال کنید.");
            }
        } catch (error) {
            setValidationError(errorMessage(error));
        }
    };

    return (
        <Stack spacing={2} sx={{mt: 2}}>
            <Divider />
            <Typography sx={{fontWeight: 700}}>ثبت مصرف واقعی مواد سفارش</Typography>
            <Alert severity="info">
                مقدار استاندارد فقط برآورد دستور تهیه است. مقدار زیر باید مصرف واقعی این مرحله باشد؛ ثبت آن موجودی را از طریق گردش انبار کاهش می‌دهد.
            </Alert>

            {requirementsQuery.isLoading && (
                <Stack direction="row" spacing={1} sx={{alignItems: "center"}}>
                    <CircularProgress size={20} />
                    <Typography variant="body2">در حال دریافت مواد موردنیاز سفارش...</Typography>
                </Stack>
            )}
            {requirementsQuery.isError && (
                <Alert severity="error">دریافت مواد موردنیاز ناموفق بود: {errorMessage(requirementsQuery.error)}</Alert>
            )}
            {requirementsQuery.isSuccess && requirements.length === 0 && (
                <Alert severity="warning">
                    برای این سفارش snapshot مواد قابل ثبت پیدا نشد؛ تا زمان بررسی سفارش نمی‌توان آن را آماده تحویل کرد.
                </Alert>
            )}

            {requirements.map((line) => (
                <Stack key={line.requirementId} spacing={1.25} sx={{borderBottom: 1, borderColor: "divider", pb: 2}}>
                    <Typography sx={{fontWeight: 600}}>
                        {line.menuItemName} — {line.ingredientName}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        مقدار استاندارد: {line.standardQuantity} {displayUnit(line.unit)} · مصرف واقعی ثبت‌شده: {line.actualQuantity} {displayUnit(line.unit)}
                    </Typography>
                    <TextField
                        label={`مصرف واقعی در این ثبت (${displayUnit(line.unit)})`}
                        type="number"
                        value={quantities[line.requirementId] ?? ""}
                        onChange={(event) => {
                            setQuantities((previous) => ({...previous, [line.requirementId]: event.target.value}));
                            setValidationError(null);
                            setSuccess(false);
                        }}
                        slotProps={{htmlInput: {min: 0, step: "any", inputMode: "decimal"}}}
                        required
                        fullWidth
                        disabled={recordMutation.isPending || Boolean(pendingRequest) || Boolean(storageError)}
                    />
                </Stack>
            ))}

            {storageError && <Alert severity="error">{storageError}</Alert>}
            {pendingRequest && <Alert severity="warning">
                یک درخواست مصرف قبلی هنوز تعیین تکلیف نشده است. فقط همان payload با همان شناسه امن قابل ارسال مجدد است.
            </Alert>}
            {validationError && <Alert severity="error">{validationError}</Alert>}
            {success && <Alert severity="success">مصرف واقعی ثبت شد و گردش موجودی به‌روزرسانی شد.</Alert>}

            {requirements.length > 0 && (
                <LoadingButton
                    type="button"
                    variant="outlined"
                    loading={recordMutation.isPending}
                    disabled={recordMutation.isPending || requirementsQuery.isLoading || requirementsQuery.isFetching || requirementsQuery.isError || Boolean(storageError)}
                    onClick={submit}
                >
                    ثبت مصرف واقعی
                </LoadingButton>
            )}
        </Stack>
    );
}
