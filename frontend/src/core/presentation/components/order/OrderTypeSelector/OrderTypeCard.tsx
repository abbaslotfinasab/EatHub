// presentation/components/order/OrderTypeSelector/OrderTypeCard.tsx

import type { ElementType } from "react";

import {
    Paper,
    Stack,
    Typography,
} from "@mui/material";

interface OrderTypeCardProps {
    title: string;

    description: string;

    icon: ElementType;

    selected: boolean;

    onClick(): void;
}

export const OrderTypeCard = ({
    title,
    description,
    icon: Icon,
    selected,
    onClick,
}: OrderTypeCardProps) => {

    return (

        <Paper
            elevation={0}
            onClick={onClick}
            sx={{
                flex: 1,

                p: 2.5,

                cursor: "pointer",

                borderRadius: 3,

                border: "2px solid",

                borderColor: selected
                    ? "primary.main"
                    : "divider",

                bgcolor: selected
                    ? "primary.50"
                    : "background.paper",

                transition: ".2s ease",

                "&:hover": {
                    borderColor: "primary.main",
                    transform: "translateY(-2px)",
                    boxShadow: 2,
                },
            }}
        >

            <Stack
                sx={{
                    alignItems: "center",
                    gap: 1.5,
                }}
            >

                <Icon
                    sx={{
                        fontSize: 34,

                        color: selected
                            ? "primary.main"
                            : "text.secondary",
                    }}
                />

                <Typography
                    sx={{
                        fontWeight: 700,
                        textAlign: "center",
                    }}
                >
                    {title}
                </Typography>

                <Typography
                    variant="caption"
                    sx={{
                        color: "text.secondary",
                        textAlign: "center",
                    }}
                >
                    {description}
                </Typography>

            </Stack>

        </Paper>

    );

};