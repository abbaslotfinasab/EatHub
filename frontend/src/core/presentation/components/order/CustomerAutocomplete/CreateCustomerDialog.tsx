// presentation/components/order/customer/CreateCustomerDialog.tsx

import { useEffect } from "react";

import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Stack,
    TextField,
} from "@mui/material";

import { Controller, useForm } from "react-hook-form";

export interface CreateCustomerDialogValues {
    name: string;
    phone: string;
}

interface CreateCustomerDialogProps {
    open: boolean;

    initialName?: string;

    loading?: boolean;

    onClose(): void;

    onSubmit(
        values: CreateCustomerDialogValues,
    ): Promise<void> | void;
}

export const CreateCustomerDialog = ({
    open,
    initialName,
    loading = false,
    onClose,
    onSubmit,
}: CreateCustomerDialogProps) => {

    const {
        control,
        handleSubmit,
        reset,
    } =
        useForm<CreateCustomerDialogValues>({
            defaultValues: {
                name: initialName ?? "",
                phone: "",
            },
        });

    useEffect(() => {

        reset({
            name: initialName ?? "",
            phone: "",
        });

    }, [
        initialName,
        open,
        reset,
    ]);

    return (

        <Dialog
            open={open}
            onClose={onClose}
            fullWidth
            maxWidth="xs"
        >

            <DialogTitle>

                ایجاد مشتری جدید

            </DialogTitle>

            <DialogContent>

                <Stack
                    spacing={2}
                    sx={{
                        pt: 1,
                    }}
                >

                    <Controller
                        control={control}
                        name="name"
                        render={({ field }) => (

                            <TextField
                                {...field}
                                label="نام مشتری"
                            />

                        )}
                    />

                    <Controller
                        control={control}
                        name="phone"
                        render={({ field }) => (

                            <TextField
                                {...field}
                                label="شماره تماس"
                                dir="ltr"
                            />

                        )}
                    />

                </Stack>

            </DialogContent>

            <DialogActions>

                <Button
                    onClick={onClose}
                >
                    انصراف
                </Button>

                <Button
                    variant="contained"
                    disabled={loading}
                    onClick={handleSubmit(onSubmit)}
                >
                    ثبت مشتری
                </Button>

            </DialogActions>

        </Dialog>

    );

};