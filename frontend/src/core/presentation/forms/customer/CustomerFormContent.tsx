import {Controller, useFormContext} from "react-hook-form";
import {
    Card,
    CardContent,
    Grid,
    Stack,
    TextField,
    Typography,
} from "@mui/material";

import type {CustomerFormInput} from "./CustomerFormInput";

export function CustomerFormContent() {
    const {
        control,
    } = useFormContext<CustomerFormInput>();

    return (
        <Card variant="outlined">
            <CardContent>
                <Stack spacing={3}>
                    <Typography
                        variant="h6"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        اطلاعات مشتری
                    </Typography>

                    <Grid
                        container
                        spacing={2}
                    >
                        <Grid
                            size={{
                                xs: 12,
                            }}
                        >
                            <Controller
                                name="name"
                                control={control}
                                render={({
                                             field,
                                             fieldState,
                                         }) => (
                                    <TextField
                                        {...field}
                                        fullWidth
                                        label="نام مشتری"
                                        placeholder="نام مشتری را وارد کنید"
                                        error={!!fieldState.error}
                                        helperText={fieldState.error?.message}
                                    />
                                )}
                            />
                        </Grid>

                        <Grid
                            size={{
                                xs: 12,
                            }}
                        >
                            <Controller
                                name="phone"
                                control={control}
                                render={({
                                             field,
                                             fieldState,
                                         }) => (
                                    <TextField
                                        {...field}
                                        fullWidth
                                        label="شماره موبایل"
                                        placeholder="09123456789"
                                        error={!!fieldState.error}
                                        helperText={fieldState.error?.message}
                                        slotProps={{
                                            htmlInput: {
                                                dir: "ltr",
                                                maxLength: 11,
                                            },
                                        }}
                                    />
                                )}
                            />
                        </Grid>
                    </Grid>
                </Stack>
            </CardContent>
        </Card>
    );
}