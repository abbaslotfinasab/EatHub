import {useEffect} from "react";
import {
    FormProvider,
    useFieldArray,
    useForm,
    type SubmitHandler,
} from "react-hook-form";
import {zodResolver} from "@hookform/resolvers/zod";
import {
    Container, Fab,
    Stack,
} from "@mui/material";

import {MenuInfoCard} from "./MenuInfoCard";
import {MenuItemsSection} from "./MenuItemsSection";

import {
    MenuFormSchema,
    type MenuFormInput,
} from "../../../forms/menu/MenuFormInput.ts";
import AddIcon from "@mui/icons-material/Add";
import {defaultMenuItem} from "../../../forms/menu/menuItemDefault.ts";

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
  items: [defaultMenuItem]
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

    const {control, handleSubmit, reset} = methods;

    const {fields, append, remove} = useFieldArray({
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
            <Container maxWidth="lg" sx={{py: 4}}>
                <Stack
                    component="form"
                    spacing={3}
                    onSubmit={handleSubmit(
                        onSubmit,
                        (errors) => {
                            console.log(errors);
                        }
                    )}
                    noValidate
                >
                    <MenuInfoCard
                        mode={mode}
                        loading={loading}
                    />

                    <MenuItemsSection
                        fields={fields}
                        remove={remove}
                    />
                </Stack>

                <Fab
                variant="extended"
                onClick={() => append({ ...defaultMenuItem })
                }
                sx={{
                    position:
                        "fixed",

                    left: 24,
                    bottom: 24,

                    bgcolor:
                        "#10281A",

                    color: "#fff",

                    "&:hover": {
                        bgcolor:
                            "#173724",
                    },
                }}
            >
                <AddIcon/>
                آیتم جدید
            </Fab>
            </Container>
        </FormProvider>
    );
}