import { useMemo, useState } from "react";

import {
    Autocomplete,
    TextField,
} from "@mui/material";

import type { Customer } from "../../../../domain/entities/product/customer/Customer";

import { useOrderForm } from "../../../forms/order/useOrderForm";

import { useSearchCustomers } from "../../../hooks/customer/useSearchCustomers";
import { useGetCustomerById } from "../../../hooks/customer/useGetCustomerById";
import { useCreateCustomer } from "../../../hooks/customer/useCreateCustomer";

import { CustomerOption } from "./CustomerOption";
import { CustomerCreateButton } from "./CustomerCreateButton";
import {
    CreateCustomerDialog,
    type CreateCustomerDialogValues,
} from "./CreateCustomerDialog";

export const CustomerAutocomplete = () => {

    const {
        watch,
        setValue,
    } = useOrderForm();

    const customerId =
        watch("customerId");

    const [keyword, setKeyword] =
        useState("");

    const [dialogOpen, setDialogOpen] =
        useState(false);

    // ====================================
    // Selected customer (Edit Mode)
    // ====================================

    const {
        data: customerDetail,
    } = useGetCustomerById(
        customerId?.toString(),
    );

    const selectedCustomer =
        customerDetail?.customer ?? null;

    // ====================================
    // Search
    // ====================================

    const {
        data: customers = [],
        isLoading,
    } = useSearchCustomers(
        keyword,
    );

    // ====================================
    // Merge Options
    // ====================================

    const options = useMemo(() => {

        if (!selectedCustomer) {
            return customers;
        }

        const exists =
            customers.some(
                x =>
                    x.id ===
                    selectedCustomer.id,
            );

        if (exists) {
            return customers;
        }

        return [
            selectedCustomer,
            ...customers,
        ];

    }, [
        customers,
        selectedCustomer,
    ]);

    // ====================================
    // Create Customer
    // ====================================

    const createCustomer =
        useCreateCustomer();

    const handleCreateCustomer = async (
        values: CreateCustomerDialogValues,
    ) => {

        const customer =
            await createCustomer.mutateAsync(
                values,
            );

        setValue(
            "customerId",
            customer.id,
        );

        setKeyword(
            customer.name,
        );

        setDialogOpen(false);

    };

    // ====================================
    // Render
    // ====================================

    return (
        <>
            <Autocomplete<Customer>

                fullWidth

                loading={isLoading}

                loadingText="در حال جستجو..."

                options={options}

                value={selectedCustomer}

                filterOptions={(x) => x}

                isOptionEqualToValue={(
                    option,
                    value,
                ) =>
                    option.id === value.id
                }

                getOptionLabel={(option) =>
                    option.name
                }

                onInputChange={(
                    _,
                    value,
                    reason,
                ) => {

                    if (
                        reason === "input"
                    ) {
                        setKeyword(value);
                    }

                }}

                onChange={(
                    _,
                    customer,
                ) => {

                    setValue(
                        "customerId",
                        customer?.id,
                    );

                }}

                renderInput={(params) => (

                    <TextField
                        {...params}
                        label="مشتری"
                        placeholder="نام یا شماره تماس..."
                    />

                )}

                renderOption={(
                    props,
                    customer,
                ) => (

                    <CustomerOption
                        {...props}
                        customer={customer}
                    />

                )}

                noOptionsText={

                    <CustomerCreateButton
                        search={keyword}
                        onClick={() =>
                            setDialogOpen(true)
                        }
                    />

                }

            />

            <CreateCustomerDialog

                open={dialogOpen}

                initialName={keyword}

                loading={
                    createCustomer.isPending
                }

                onClose={() =>
                    setDialogOpen(false)
                }

                onSubmit={
                    handleCreateCustomer
                }

            />
        </>
    );

};