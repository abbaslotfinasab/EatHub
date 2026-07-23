import {
    Card,
    CardContent,
    Stack,
    Typography,
    Divider,
} from "@mui/material";

import LocalFireDepartmentIcon from "@mui/icons-material/LocalFireDepartment";

import {TopProductItem} from "./TopProductItem";
import type {TopProduct} from "../../../domain/entities/account/TopProduct";

interface TopProductsProps {
    products: TopProduct[];
}

export const TopProducts = ({
                                products,
                            }: TopProductsProps) => {

    const maxSold =
        Math.max(
            ...products.map(
                (item) => item.totalSold
            ),
            1
        );


    return (
        <Card
            elevation={0}
            sx={{
                borderRadius: 4,
                border: "1px solid",
                borderColor: "divider",
                height: "100%",
            }}
        >
            <CardContent>

                <Stack spacing={3}>

                    <Stack
                        direction="row"
                        sx={{
                            alignItems: "center",
                            gap: 1,
                        }}
                    >
                        <LocalFireDepartmentIcon
                            color="warning"
                        />

                        <Typography
                            variant="h6"
                            sx={{
                                fontWeight: 700,
                            }}
                        >
                            پرفروش‌ترین غذاها
                        </Typography>

                    </Stack>


                    {products.map(
                        (product, index) => (

                            <Stack
                                key={product.menuItemId}
                                spacing={2}
                            >

                                <TopProductItem
                                    name={product.name}
                                    orderCount={product.totalSold}
                                    percentage={
                                        Math.round(
                                            (
                                                product.totalSold /
                                                maxSold
                                            ) * 100
                                        )
                                    }
                                    revenue={product.revenue}
                                />


                                {
                                    index !== products.length - 1 && (
                                        <Divider/>
                                    )
                                }

                            </Stack>

                        )
                    )}

                </Stack>

            </CardContent>
        </Card>
    );
};