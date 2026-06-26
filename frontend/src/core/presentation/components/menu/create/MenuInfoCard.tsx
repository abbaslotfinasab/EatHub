// src/presentation/components/menu/MenuInfoCard.tsx

import {Box, Card, CardContent, Divider, Grid, Stack, Typography} from "@mui/material";
import {FormTextarea} from "../../form/FormTextarea.tsx";
import { LoadingButton } from "@mui/lab";
import {FormInput} from "../../form/FormInput.tsx";
import {MenuIcon, Save} from "lucide-react";


interface Props {
    loading?: boolean;
    mode: "create" | "edit";
}
export const MenuInfoCard = ({loading = false}: Props) => {
    return (
        <Card elevation={0}>
            <Box
                sx={{
                    bgcolor: "#10281A",
                    px: 3,
                    py: 2.5,
                    borderBottom: "1px solid",
                    borderColor: "divider",
                }}
            >
                <Stack
                    sx={{
                        flexDirection: "row",
                        justifyContent: "space-between",
                        alignItems: "center",
                    }}
                >
                    <Stack
                        sx={{
                            flexDirection: "row",
                            gap: 1,
                            alignItems: "center",
                        }}
                    >
                        <MenuIcon
                            size={20}
                            color="rgba(255,255,255,.85)"
                        />

                        <Typography
                            sx={{
                                typography: "h6",
                                fontWeight: 600,
                                color: "white",
                            }}
                        >
                            اطلاعات منو
                        </Typography>
                    </Stack>

                    <LoadingButton
                        loading={loading}
                        type="submit"
                        variant="contained"
                        endIcon={<Save size={16}/>}
                        sx={{
                            bgcolor: "white",
                            color: "#10281A",
                            px: 2,
                            py: 1,
                            borderRadius: 2,
                            fontWeight: 600,
                            boxShadow: "none",

                            "& .MuiButton-endIcon": {
                                mr: 1,
                                ml: 0,
                            },

                            "&:hover": {
                                bgcolor: "grey.100",
                                boxShadow: "none",
                            },
                        }}
                    >
                        ذخیره منو
                    </LoadingButton>
                </Stack>
            </Box>

            <Divider/>

            <CardContent>
                <Grid container spacing={3}>
                    <Grid size={{xs: 12, md: 6}}>
                        <FormInput
                            name="name"
                            label="نام منو"
                            placeholder="مثلاً منوی صبحانه"
                        />
                    </Grid>

                    <Grid size={{xs: 12, md: 6}}>
                        <FormInput
                            name="category"
                            label="دسته‌بندی"
                            placeholder="مثلاً غذا، نوشیدنی، دسر"
                        />
                    </Grid>

                    <Grid size={{xs: 12, md: 8}}>
                        <FormTextarea
                            name="description"
                            label="توضیحات"
                            rows={3}
                            placeholder="توضیحات اختیاری درباره این منو..."
                        />
                    </Grid>

                    <Grid size={{xs: 12, md: 4}}>
                        <FormInput
                            name="sortOrder"
                            type="number"
                            label="ترتیب نمایش"
                        />
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    );
};