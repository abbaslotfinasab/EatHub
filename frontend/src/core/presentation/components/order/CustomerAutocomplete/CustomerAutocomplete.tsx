// presentation/components/order/customer/CustomerAutocomplete.tsx

import {useState} from "react";


import {
    Autocomplete,
    TextField,
} from "@mui/material";

import {useOrderForm} from "../../../forms/order/useOrderForm";

import {useSearchCustomers} from "../../../hooks/customer/useSearchCustomers";

import {CustomerOption} from "./CustomerOption";
import {
    CreateCustomerDialog,
    type CreateCustomerDialogValues,
} from "./CreateCustomerDialog";

import {CustomerCreateButton} from "./CustomerCreateButton.tsx";
import type {Customer} from "../../../../domain/entities/product/customer/Customer.ts";
import {useCreateCustomer} from "../../../hooks/customer/useCreateCustomer.ts";

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

    // ==========================
    // Search
    // ==========================

    const {
        data: customers = [],
        isLoading,
    } = useSearchCustomers(keyword);

    // ==========================
    // Create
    // ==========================

    const createCustomer =
        useCreateCustomer();

    const handleCreateCustomer = async (
    values: CreateCustomerDialogValues,
) => {

    const customer =
        await createCustomer.mutateAsync(values);

    setValue(
        "customerId",
        customer.id,
    );

    setKeyword(
        customer.name,
    );

    setDialogOpen(false);

};

    // ==========================
    // Selected Customer
    // ==========================

    const selectedCustomer =
        customers.find(
            x => x.id === customerId,
        ) ?? null;

    return (
        <>

            <Autocomplete<Customer>

                loadingText="در حال جستجو..."

                fullWidth

                options={customers}

                value={selectedCustomer}

                loading={isLoading}

                filterOptions={(x) => x}

                isOptionEqualToValue={(
                    a,
                    b,
                ) =>
                    a.id === b.id
                }

                getOptionLabel={(option) =>
                    option.name
                }

                onInputChange={(
                    _,
                    value,
                ) => {

                    setKeyword(value);

                }}

                onChange={(
                    _,
                    customer,
                ) => {

                    if (!customer) {

                        setValue(
                            "customerId",
                            undefined,
                        );

                        return;

                    }

                    setValue(
                        "customerId",
                        customer.id,
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
                        customer={
                            customer
                        }
                    />

                )}

                noOptionsText={
                    <CustomerCreateButton
                        search={keyword}
                        onClick={() => setDialogOpen(true)}
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
                    setDialogOpen(
                        false,
                    )
                }
                onSubmit={
                    handleCreateCustomer
                }
            />

        </>
    );

};