import { useEffect } from "react";
import {
    FormProvider,
    useFieldArray,
    useForm,
    type SubmitHandler,
} from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import {
    Container,
    Stack,
} from "@mui/material";

import { MenuInfoCard } from "./MenuInfoCard";
import { MenuItemsSection } from "./MenuItemsSection";

import {
    MenuFormSchema,
    type MenuFormInput,
} from "../../../../domain/objects/forms/MenuFormInput";

interface MenuFormProps {
    mode: "create" | "edit";
    loading?: boolean;
    initialData?: MenuFormInput;
    onSubmit: SubmitHandler<MenuFormInput>;
}

const defaultValues: MenuFormInput = {
    name: "",
    category: "",
    description: null,
    sortOrder: 0,
    isActive: true,
    items: [
        {
            name: "",
            description: null,
            price: 0,
            imageFile: null,
            imageUrl: null,
            isAvailable: true,
        },
    ],
};

export function MenuForm({
    mode,
    loading = false,
    initialData,
    onSubmit,
}: MenuFormProps) {

    const methods = useForm<MenuFormInput>({
        defaultValues,
        resolver: zodResolver(MenuFormSchema),
    });

    const { control, handleSubmit, reset } = methods;

    const { fields, append, remove } = useFieldArray({
        control,
        name: "items",
    });


    useEffect(() => {
        if (initialData) {
            reset(initialData);
        }
    }, [initialData, reset]);

    return (
        <FormProvider {...methods}>
            <Container maxWidth="lg" sx={{ py: 4 }}>
                <Stack
                    component="form"
                    spacing={3}
                    onSubmit={handleSubmit(onSubmit)}
                    noValidate
                >
                    <MenuInfoCard
                        mode={mode}
                        loading={loading}
                    />

                    <MenuItemsSection
                        fields={fields}
                        append={append}
                        remove={remove}
                    />
                </Stack>
            </Container>
        </FormProvider>
    );
}