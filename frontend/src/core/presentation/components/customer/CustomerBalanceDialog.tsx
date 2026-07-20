import {
    Avatar,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    MenuItem,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import {LoadingButton} from "@mui/lab";

import type {CustomerListItem} from "../../../domain/entities/product/customer/CustomerListItem.ts";


import {formatCurrency} from "../../utils/formatCurrency.ts";
import {CustomerBalanceOperation} from "../../../domain/objects/CustomerBalanceOperation.ts";


interface CustomerBalanceDialogProps {

    open: boolean;

    customer?: CustomerListItem | null;

    operation: CustomerBalanceOperation;

    amount: string;

    description: string;

    loading?: boolean;

    onClose(): void;

    onOperationChange(
        value: CustomerBalanceOperation,
    ): void;

    onAmountChange(
        value: string,
    ): void;

    onDescriptionChange(
        value: string,
    ): void;

    onSubmit(): void;

}


export function CustomerBalanceDialog({

                                          open,

                                          customer,

                                          operation,

                                          amount,

                                          description,

                                          loading = false,

                                          onClose,

                                          onOperationChange,

                                          onAmountChange,

                                          onDescriptionChange,

                                          onSubmit,

                                      }: CustomerBalanceDialogProps) {


    if (!customer) {
        return null;
    }


    const submitLabel = {

        [CustomerBalanceOperation.CREDIT]:
            "شارژ حساب",

        [CustomerBalanceOperation.DEBIT]:
            "برداشت از حساب",

        [CustomerBalanceOperation.ADJUST]:
            "اصلاح موجودی",

    }[operation];


    const buttonColor =
        operation === CustomerBalanceOperation.CREDIT
            ? "success"
            : operation === CustomerBalanceOperation.DEBIT
                ? "error"
                : "warning";


    return (

        <Dialog
            open={open}
            onClose={onClose}
            fullWidth
            maxWidth="sm"
        >

            <DialogTitle>
                مدیریت حساب مشتری
            </DialogTitle>


            <DialogContent>

                <Stack
                    sx={{
                        gap: 3,
                        mt: 1,
                    }}
                >

                    <Stack
                        sx={{
                            flexDirection: "row",
                            alignItems: "center",
                            gap: 2,
                        }}
                    >

                        <Avatar
                            sx={{
                                bgcolor: "primary.main",
                                width: 48,
                                height: 48,
                                fontWeight: 700,
                            }}
                        >
                            {
                                customer.name.charAt(0)
                            }
                        </Avatar>


                        <Stack
                            sx={{
                                gap: 0.5,
                            }}
                        >
                            <Typography
                                sx={{
                                    fontWeight: 700,
                                }}
                            >
                                {customer.name}
                            </Typography>

                            <Typography
                                variant="body2"
                                color="text.secondary"
                            >
                                {
                                    customer.phone
                                }
                            </Typography>

                        </Stack>

                    </Stack>


                    <TextField

                        label="موجودی فعلی"

                        value={
                            formatCurrency(
                                customer.balance ?? 0,
                            )
                        }

                        slotProps={{
                            input: {
                                readOnly: true,
                            },
                        }}

                    />


                    <TextField

                        select

                        label="نوع عملیات"

                        value={operation}

                        onChange={(e) =>
                            onOperationChange(
                                e.target.value as CustomerBalanceOperation,
                            )
                        }

                    >

                        <MenuItem
                            value={
                                CustomerBalanceOperation.CREDIT
                            }
                        >
                            شارژ حساب
                        </MenuItem>


                        <MenuItem
                            value={
                                CustomerBalanceOperation.DEBIT
                            }
                        >
                            برداشت از حساب
                        </MenuItem>


                        <MenuItem
                            value={
                                CustomerBalanceOperation.ADJUST
                            }
                        >
                            اصلاح موجودی
                        </MenuItem>


                    </TextField>


                    <TextField

                        label="مبلغ"

                        value={amount}

                        onChange={(e) =>
                            onAmountChange(
                                e.target.value,
                            )
                        }

                        type="number"

                        fullWidth

                    />


                    <TextField

                        label="توضیحات"

                        multiline

                        minRows={3}

                        value={description}

                        onChange={(e) =>
                            onDescriptionChange(
                                e.target.value,
                            )
                        }

                    />


                </Stack>

            </DialogContent>


            <DialogActions>

                <Button
                    onClick={onClose}
                >
                    انصراف
                </Button>


                <LoadingButton

                    loading={loading}

                    variant="contained"

                    color={buttonColor}

                    onClick={onSubmit}

                >

                    {submitLabel}

                </LoadingButton>


            </DialogActions>


        </Dialog>

    );

}