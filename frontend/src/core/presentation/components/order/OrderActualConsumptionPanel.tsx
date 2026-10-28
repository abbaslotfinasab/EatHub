import {useRef, useState} from "react";
import {isAxiosError} from "axios";
import {Alert, CircularProgress, Divider, Stack, TextField, Typography} from "@mui/material";
import {LoadingButton} from "@mui/lab";
import type {UseQueryResult} from "@tanstack/react-query";

import {useRecordOrderConsumption} from "../../hooks/order/useRecordOrderConsumption.ts";
import type {OrderConsumptionRequirements} from "../../../domain/entities/product/order/OrderInventoryConsumption.ts";

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
    const attempt = useRef<{intent: string; key: string} | null>(null);

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

        const lines = requirements.map((line) => ({
            requirementId: line.requirementId,
            quantity: quantities[line.requirementId].trim(),
            unit: line.unit,
        }));
        const intent = JSON.stringify([orderId, lines]);
        const idempotencyKey = attempt.current?.intent === intent
            ? attempt.current.key
            : crypto.randomUUID();
        attempt.current = {intent, key: idempotencyKey};

        try {
            await recordMutation.mutateAsync({orderId, idempotencyKey, lines});
            attempt.current = null;
            setQuantities({});
            setSuccess(true);
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
                        disabled={recordMutation.isPending}
                    />
                </Stack>
            ))}

            {validationError && <Alert severity="error">{validationError}</Alert>}
            {success && <Alert severity="success">مصرف واقعی ثبت شد و گردش موجودی به‌روزرسانی شد.</Alert>}

            {requirements.length > 0 && (
                <LoadingButton
                    type="button"
                    variant="outlined"
                    loading={recordMutation.isPending}
                    disabled={recordMutation.isPending || requirementsQuery.isLoading || requirementsQuery.isFetching || requirementsQuery.isError}
                    onClick={submit}
                >
                    ثبت مصرف واقعی
                </LoadingButton>
            )}
        </Stack>
    );
}
