import {type ReactNode, useEffect} from "react";
import {Stack} from "@mui/material";
import {FormProvider, useForm} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";

import {CustomerFormContent} from "./CustomerFormContent";
import {
    type CustomerFormInput,
    CustomerFormSchema,
} from "./CustomerFormInput";

interface CustomerFormProps {
    initialValues?: Partial<CustomerFormInput>;

    onSubmit(values: CustomerFormInput): void;

    children?(submit: () => void): ReactNode;
}

const DEFAULT_VALUES: CustomerFormInput = {
    name: "",
    phone: "",
};

export function CustomerForm({
    initialValues,
    onSubmit,
    children,
}: CustomerFormProps) {

    const methods = useForm<CustomerFormInput>({
        resolver: zodResolver(CustomerFormSchema),
        defaultValues: {
            ...DEFAULT_VALUES,
            ...initialValues,
        },
        mode: "onChange",
    });

    const {
        reset,
        handleSubmit,
    } = methods;

    useEffect(() => {
        reset({
            ...DEFAULT_VALUES,
            ...initialValues,
        });
    }, [initialValues, reset]);

    return (
        <FormProvider {...methods}>
            <Stack
                component="form"
                spacing={3}
                onSubmit={handleSubmit(onSubmit)}
            >
                <CustomerFormContent/>

                {children?.(handleSubmit(onSubmit))}
            </Stack>
        </FormProvider>
    );
}