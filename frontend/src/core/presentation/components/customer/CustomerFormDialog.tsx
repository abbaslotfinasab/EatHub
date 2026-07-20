import {Button, Dialog, DialogActions, DialogContent, DialogTitle} from "@mui/material";
import {LoadingButton} from "@mui/lab";

import type {CustomerFormInput} from "../../forms/customer/CustomerFormInput";
import {CustomerForm} from "../../forms/customer/CustomerForm";

interface CustomerFormDialogProps {
    open: boolean;

    initialValues?: CustomerFormInput;

    loading?: boolean;

    title?: string;

    onClose(): void;

    onSubmit(values: CustomerFormInput): void;
}

export function CustomerFormDialog({
    open,
    initialValues,
    loading = false,
    title = "مشتری جدید",
    onClose,
    onSubmit,
}: CustomerFormDialogProps) {
    return (
        <Dialog
            open={open}
            onClose={onClose}
            fullWidth
            maxWidth="sm"
        >
            <DialogTitle>
                {title}
            </DialogTitle>

            <DialogContent dividers>
                <CustomerForm
                    initialValues={initialValues}
                    onSubmit={onSubmit}
                >
                    {(submit) => (
                        <DialogActions sx={{px: 0, pt: 3}}>
                            <Button onClick={onClose}>
                                انصراف
                            </Button>

                            <LoadingButton
                                loading={loading}
                                variant="contained"
                                onClick={submit}
                            >
                                ذخیره
                            </LoadingButton>
                        </DialogActions>
                    )}
                </CustomerForm>
            </DialogContent>
        </Dialog>
    );
}