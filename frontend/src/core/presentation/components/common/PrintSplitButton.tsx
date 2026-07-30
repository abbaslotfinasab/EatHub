import { useState } from "react";

import {
    Button,
    ButtonGroup,
    ClickAwayListener,
    Grow,
    MenuItem,
    MenuList,
    Paper,
    Popper,
} from "@mui/material";

import PrintRoundedIcon from "@mui/icons-material/PrintRounded";
import ArrowDropDownRoundedIcon from "@mui/icons-material/ArrowDropDownRounded";

export interface PrintMenuItem {

    label: string;

    onClick(): void;

}

interface PrintSplitButtonProps {

    items: PrintMenuItem[];

    loading?: boolean;

}

export function PrintSplitButton({

    items,

    loading = false,

}: PrintSplitButtonProps) {

   const [anchorEl, setAnchorEl] =
    useState<HTMLElement | null>(null);

    const open =
        Boolean(anchorEl);

    const handleToggle = (
        event: React.MouseEvent<HTMLButtonElement>,
    ) => {

        setAnchorEl(prev =>
            prev ? null : event.currentTarget.parentElement,
        );

    };

    const handleClose = () => {

        setAnchorEl(null);

    };

    const handlePrimaryClick = () => {

        items[0]?.onClick();

    };

    return (

        <>

            <ButtonGroup
                variant="contained"
                disableElevation
                sx={{

                    borderRadius: 2,

                    overflow: "hidden",

                    boxShadow: 2,

                    "& .MuiButton-root": {

                        px: 2,

                        py: 1.2,

                        fontWeight: 700,

                        textTransform: "none",

                    },

                }}
            >

                <Button
                    loading={loading}
                    startIcon={<PrintRoundedIcon />}
                    onClick={handlePrimaryClick}
                >
                    چاپ
                </Button>

                <Button
                    size="small"
                    onClick={handleToggle}
                    sx={{
                        minWidth: 42,
                    }}
                >
                    <ArrowDropDownRoundedIcon />
                </Button>

            </ButtonGroup>

            <Popper
                open={open}
                anchorEl={anchorEl}
                transition
                placement="bottom-start"
                sx={{
                    zIndex: 1500,
                }}
            >

                {({ TransitionProps }) => (

                    <Grow {...TransitionProps}>

                        <Paper
                            elevation={6}
                            sx={{
                                mt: 1,
                                minWidth: 220,
                                borderRadius: 2,
                                overflow: "hidden",
                            }}
                        >

                            <ClickAwayListener
                                onClickAway={handleClose}
                            >

                                <MenuList>

                                    {items.map((item, index) => (

                                        <MenuItem
                                            key={index}
                                            onClick={() => {

                                                handleClose();

                                                item.onClick();

                                            }}
                                        >

                                            {item.label}

                                        </MenuItem>

                                    ))}

                                </MenuList>

                            </ClickAwayListener>

                        </Paper>

                    </Grow>

                )}

            </Popper>

        </>

    );

}