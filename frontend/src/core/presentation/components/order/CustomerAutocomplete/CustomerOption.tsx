// presentation/components/order/customer/CustomerOption.tsx

import {
    Avatar,
    Box,
    Stack,
    Typography,
} from "@mui/material";

import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import PhoneRoundedIcon from "@mui/icons-material/PhoneRounded";

import type {HTMLAttributes} from "react";
import type {Customer} from "../../../../domain/entities/product/customer/Customer.ts";


interface CustomerOptionProps
    extends HTMLAttributes<HTMLLIElement> {

    customer: Customer;
}

export const CustomerOption = ({
                                   customer,
                                   ...props
                               }: CustomerOptionProps) => {

    return (

        <Box
            component="li"
            {...props}
            sx={{
                listStyle: "none",
                px: 2,
                py: 1.5,
                cursor: "pointer",

                "&:hover": {
                    bgcolor: "action.hover",
                },

                ...props.style,
            }}
        >

            <Stack
                sx={{
                    flexDirection: "row",
                    gap: 2,
                    alignItems: "center",
                }}
            >
                <Avatar
                    sx={{
                        bgcolor: "primary.main",
                        width: 42,
                        height: 42,
                    }}
                >
                    <PersonRoundedIcon/>
                </Avatar>

                <Stack
                    sx={{
                        flex: 1,
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

                    <Stack
                        sx={{
                            flexDirection: "row",
                            gap: 0.5,
                            alignItems: "center",
                        }}
                    >
                        <PhoneRoundedIcon
                            sx={{
                                fontSize: 16,
                                color:
                                    "text.secondary",
                            }}
                        />

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {customer.phone}
                        </Typography>

                    </Stack>

                </Stack>

            </Stack>

        </Box>

    );

};