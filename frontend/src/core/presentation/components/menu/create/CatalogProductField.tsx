import {useMemo, useState} from "react";
import {Autocomplete, TextField} from "@mui/material";
import {useFormContext, useWatch} from "react-hook-form";
import type {MenuFormInput} from "../../../forms/menu/MenuFormInput.ts";
import {useProducts} from "../../../hooks/catalog/useProducts.ts";

interface ProductOption {
    id: number;
    name: string;
    inactive?: boolean;
}

interface Props {
    index: number;
}

export const CatalogProductField = ({index}: Props) => {
    const {control, setValue} = useFormContext<MenuFormInput>();
    const productId = useWatch({control, name: `items.${index}.productId`}) ?? null;
    const productName = useWatch({control, name: `items.${index}.productName`}) ?? null;
    const [search, setSearch] = useState("");
    const {data, isLoading, isError} = useProducts(search, 1, 100);

    const options = useMemo<ProductOption[]>(() => {
        const active: ProductOption[] = (data?.results ?? [])
            .filter((product) => product.status === "active")
            .map((product) => ({id: product.id, name: product.name}));
        if (productId != null && !active.some((product) => product.id === productId)) {
            active.unshift({
                id: productId,
                name: productName ? `${productName} (اتصال فعلی)` : `محصول #${productId}`,
                inactive: true,
            });
        }
        return active;
    }, [data?.results, productId, productName]);

    const selected = options.find((product) => product.id === productId) ?? null;

    return (
        <Autocomplete<ProductOption>
            options={options}
            value={selected}
            loading={isLoading}
            getOptionLabel={(option) => option.name}
            isOptionEqualToValue={(option, value) => option.id === value.id}
            getOptionDisabled={(option) => Boolean(option.inactive)}
            onInputChange={(_, value, reason) => {
                if (reason === "input" || reason === "clear") setSearch(value);
            }}
            onChange={(_, option) => {
                setValue(`items.${index}.productId`, option?.id ?? null, {
                    shouldDirty: true,
                    shouldValidate: true,
                });
                setValue(`items.${index}.productName`, option?.name ?? null, {
                    shouldDirty: true,
                });
            }}
            noOptionsText={isError ? "دریافت محصولات ناموفق بود" : "محصول فعالی پیدا نشد"}
            loadingText="در حال دریافت محصولات..."
            renderInput={(params) => (
                <TextField
                    {...params}
                    label="محصول کاتالوگ (اختیاری)"
                    placeholder="برای جست‌وجوی محصول تایپ کنید"
                    helperText={
                        isError
                            ? "بارگذاری محصولات با خطا مواجه شد."
                            : "فقط محصولات فعال همین کسب‌وکار قابل انتخاب هستند. نام و قیمت آیتم منو مستقل باقی می‌ماند."
                    }
                />
            )}
        />
    );
};
