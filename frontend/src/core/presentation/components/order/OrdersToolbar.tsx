// presentation/components/order/OrdersToolbar.tsx

import {useMemo, useState} from "react";

import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import FilterListRoundedIcon from "@mui/icons-material/FilterListRounded";

import {
    Badge,
    Button,
    InputAdornment,
    Paper,
    Stack,
    TextField,
} from "@mui/material";


import type {
    OrderFilters,
} from "../../../domain/objects/filters/OrderFilters";


import {
    OrdersFilterPopover,
} from "./OrdersFilterPopover";



interface OrdersToolbarProps {


    search: string;


    filters: OrderFilters;



    onSearchChange: (
        value: string
    ) => void;



    onFiltersChange: (
        filters: OrderFilters
    ) => void;


}



export const OrdersToolbar = ({

    search,

    filters,

    onSearchChange,

    onFiltersChange,

}: OrdersToolbarProps) => {



    const [
        anchorEl,
        setAnchorEl
    ] = useState<HTMLElement | null>(null);




    const filtersActive = useMemo(() => {


        return Boolean(

            filters.status ||

            filters.orderType ||

            filters.paymentStatus ||

            filters.paymentMethod ||

            filters.fromDate ||

            filters.toDate ||

            (
                filters.ordering &&
                filters.ordering !== "-created_at"
            )

        );


    },[filters]);





    const handleOpenFilters = (
        event: React.MouseEvent<HTMLElement>
    ) => {

        setAnchorEl(
            event.currentTarget
        );

    };




    const handleClearFilters = () => {


        onFiltersChange({

            ordering:
                "-created_at",

        });


    };




    return (

        <>


            <Paper

                elevation={0}

                sx={{

                    p:2,

                    borderRadius:1,

                    border:"1px solid",

                    borderColor:"divider",

                    bgcolor:"background.paper",

                }}

            >


                <Stack

                    sx={{

                        flexDirection:{

                            xs:"column",

                            md:"row",

                        },


                        gap:2,


                        alignItems:"center",

                    }}

                >



                    <TextField


                        fullWidth


                        value={search}


                        placeholder="جستجوی مشتری، شماره سفارش..."


                        onChange={(e)=>

                            onSearchChange(
                                e.target.value
                            )

                        }



                        sx={{


                            "& .MuiOutlinedInput-root":{


                                height:56,

                                borderRadius:1,



                                "& fieldset":{

                                    borderColor:
                                        "#E2E8F0",

                                },



                                "&:hover fieldset":{

                                    borderColor:
                                        "#1F4A33",

                                },



                                "&.Mui-focused fieldset":{

                                    borderColor:
                                        "#10281A",

                                    borderWidth:2,

                                },


                            },


                        }}



                        slotProps={{


                            input:{


                                startAdornment:(


                                    <InputAdornment position="start">

                                        <SearchRoundedIcon/>

                                    </InputAdornment>


                                ),


                            },


                        }}



                    />





                    <Badge


                        color="primary"


                        variant="dot"


                        invisible={
                            !filtersActive
                        }


                    >



                        <Button


                            variant="outlined"


                            endIcon={

                                <FilterListRoundedIcon/>

                            }



                            onClick={
                                handleOpenFilters
                            }



                            sx={{


                                width:{

                                    xs:"100%",

                                    md:150,

                                },


                                height:56,


                                borderRadius:1,


                                flexShrink:0,



                                "& .MuiButton-endIcon":{


                                    marginRight:8,

                                    marginLeft:0,


                                },


                            }}


                        >

                            فیلترها


                        </Button>



                    </Badge>



                </Stack>



            </Paper>





            <OrdersFilterPopover


                open={
                    Boolean(anchorEl)
                }



                anchorEl={anchorEl}



                status={
                    filters.status ?? "ALL"
                }



                orderType={
                    filters.orderType ?? "ALL"
                }



                paymentStatus={
                    filters.paymentStatus ?? "ALL"
                }



                paymentMethod={
                    filters.paymentMethod ?? "ALL"
                }



                ordering={
                    filters.ordering ?? "-created_at"
                }



                fromDate={
                    filters.fromDate ?? ""
                }



                toDate={
                    filters.toDate ?? ""
                }




                onStatusChange={(value)=>{


                    onFiltersChange({

                        ...filters,

                        status:
                            value === "ALL"
                                ? undefined
                                : value,

                    });


                }}




                onOrderTypeChange={(value)=>{


                    onFiltersChange({

                        ...filters,

                        orderType:
                            value === "ALL"
                                ? undefined
                                : value,

                    });


                }}




                onPaymentStatusChange={(value)=>{


                    onFiltersChange({

                        ...filters,

                        paymentStatus:
                            value === "ALL"
                                ? undefined
                                : value,

                    });


                }}




                onPaymentMethodChange={(value)=>{


                    onFiltersChange({

                        ...filters,

                        paymentMethod:
                            value === "ALL"
                                ? undefined
                                : value,

                    });


                }}




                onOrderingChange={(value)=>{


                    onFiltersChange({

                        ...filters,

                        ordering:value,

                    });


                }}




                onFromDateChange={(value)=>{


                    onFiltersChange({

                        ...filters,

                        fromDate:value,

                    });


                }}




                onToDateChange={(value)=>{


                    onFiltersChange({

                        ...filters,

                        toDate:value,

                    });


                }}





                onClear={
                    handleClearFilters
                }





                onClose={()=>{

                    setAnchorEl(null);

                }}


            />



        </>

    );

};