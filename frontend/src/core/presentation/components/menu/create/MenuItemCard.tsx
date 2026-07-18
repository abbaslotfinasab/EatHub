// src/presentation/components/menu/MenuItemCard.tsx

import {
    Card,
    CardContent,
    Divider,
    Grid,
    IconButton,
    Stack,
    Typography,
    Box,

} from "@mui/material";

import {
    Trash2,
} from "lucide-react";

import {useWatch, useFormContext} from "react-hook-form";

import {FormTextarea} from "../../form/FormTextarea.tsx";
import {FormFile} from "../../form/FormFile.tsx";
import {FormInput} from "../../form/FormInput.tsx";
import type {MenuFormInput} from "../../../forms/menu/MenuFormInput.ts";


interface Props {
    index: number;
    onDelete: () => void;
}

export const MenuItemCard = ({
                                 index,
                                 onDelete,
                             }: Props) => {

    const {control} = useFormContext<MenuFormInput>();

    const name = useWatch({
        control,
        name: `items.${index}.name`,
    });

    const price = useWatch({
        control,
        name: `items.${index}.price`,
    });

    return (
        <Card
            elevation={0}
            sx={{
                border: "1px solid",
                borderColor: "divider",
                borderRadius: 3,
            }}
        >
            <Box
                sx={{
                    px: 3,
                    py: 2,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    borderBottom: 1,
                    borderColor: "divider",
                    bgcolor: "grey.50",
                }}
            >
                <Stack
                    sx={{
                        flexDirection: "row",
                        alignItems: "center",
                        gap: 2,
                    }}
                >
                    <Box
                        sx={{
                            width: 46,
                            height: 46,
                            borderRadius: 2,
                            bgcolor: "#10281A",
                            color: "white",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontWeight: 700,
                            fontSize: 16,
                        }}
                    >
                        {index + 1}
                    </Box>

                    <Box>
                        <Typography
                            sx={{
                                typography: "subtitle1",
                                fontWeight: 700,
                            }}
                        >
                            {name || "آیتم جدید"}
                        </Typography>

                        <Typography
                            sx={{
                                typography: "body2",
                                color: "text.secondary",
                                mt: 0.25,
                            }}
                        >
                            {price
                                ? `${Number(price).toLocaleString()} تومان`
                                : "هنوز قیمتی وارد نشده"}
                        </Typography>
                    </Box>
                </Stack>

                <Stack
                    sx={{
                        flexDirection: "row",
                        gap: 1,
                        alignItems: "center",
                    }}
                >

                    <IconButton
                        color="error"
                        onClick={onDelete}
                        sx={{
                            border: "1px solid",
                            borderColor: "error.light",
                            borderRadius: 2,

                            "&:hover": {
                                bgcolor: "error.lighter",
                            },
                        }}
                    >
                        <Trash2 size={18}/>
                    </IconButton>
                </Stack>
            </Box>

            <Divider/>

            <CardContent>
                <Grid container spacing={3}>
                    <Grid size={{xs: 12, md: 6}}>
                        <FormInput
                            name={`items.${index}.name`}
                            label="نام آیتم"
                            placeholder="مثلاً برگر ویژه"
                        />
                    </Grid>

                    <Grid size={{xs: 12, md: 6}}>
                        <FormInput
                            name={`items.${index}.price`}
                            type="number"
                            label="قیمت"
                            placeholder="250000"
                        />
                    </Grid>

                    <Grid size={{xs: 12, md: 8}}>
                        <FormTextarea
                            name={`items.${index}.description`}
                            label="توضیحات"
                            rows={4}
                        />
                    </Grid>

                    <Grid size={{xs: 12, md: 4}}>
                        <FormFile
                            name={`items.${index}.imageFile`}
                            label="تصویر آیتم"
                        />
                    </Grid>
                </Grid>
            </CardContent>
        </Card>
    );
};