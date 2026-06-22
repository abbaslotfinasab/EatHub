import {
    Card,
    CardContent,
    Stack,
    Typography,
    Divider,
} from "@mui/material";

import LocalFireDepartmentIcon from "@mui/icons-material/LocalFireDepartment";

import {TopProductItem}
    from "./TopProductItem";

export const TopProducts = () => {
    const products = [
        {
            id: "1",
            name: "پیتزا مخصوص",
            orderCount: 82,
            percentage: 68,
            revenue: 18500000,
        },
        {
            id: "2",
            name: "برگر ویژه",
            orderCount: 61,
            percentage: 51,
            revenue: 14300000,
        },
        {
            id: "3",
            name: "پاستا آلفردو",
            orderCount: 48,
            percentage: 40,
            revenue: 9200000,
        },
    ];

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
                                fontWeight:700
                            }}>
                            پرفروش‌ترین غذاها
                        </Typography>
                    </Stack>

                    {products.map(
                        (product, index) => (
                            <Stack
                                key={product.id}
                                spacing={2}
                            >
                                <TopProductItem
                                    {...product}
                                />

                                {index !==
                                    products.length -
                                    1 && (
                                        <Divider/>
                                    )}
                            </Stack>
                        )
                    )}
                </Stack>
            </CardContent>
        </Card>
    );
};