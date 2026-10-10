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

    const totalSold = products.reduce(
        (total, product) => total + product.totalSold,
        0,
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


                    {products.length === 0 ? (
                        <Typography color="text.secondary" variant="body2">
                            هنوز فروش ثبت‌شده‌ای وجود ندارد.
                        </Typography>
                    ) : products.map(
                        (product, index) => (

                            <Stack
                                key={product.menuItemId ?? `snapshot-${product.name}`}
                                spacing={2}
                            >

                                <TopProductItem
                                    name={product.name}
                                    soldCount={product.totalSold}
                                    ordersCount={product.ordersCount}
                                    percentage={
                                        totalSold > 0
                                            ? Math.round(product.totalSold / totalSold * 100)
                                            : 0
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
