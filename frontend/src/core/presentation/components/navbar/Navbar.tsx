import {
    AppBar,
    Toolbar,
    Box,
    Button,
    Container,
} from "@mui/material";

import { useNavigate } from "react-router-dom";
import { NavbarLogo } from "./NavbarLogo";

export const Navbar = () => {
    const navigate = useNavigate();

    return (
        <AppBar
            position="fixed"
            elevation={0}
            sx={{
                bgcolor: "rgba(255,255,255,.7)",
                backdropFilter: "blur(16px)",
                borderBottom: "1px solid #F1F5F9",
            }}
        >
            <Container maxWidth="xl">
                <Toolbar
                    sx={{
                        height: 80,
                        display: "flex",
                        justifyContent: "space-between",
                    }}
                >
                    {/* Logo */}
                    <NavbarLogo />

                    {/* Action */}
                    <Box>
                        <Button
                            variant="text"
                            onClick={() => navigate("/login")}
                            sx={{
                                fontWeight: 700,
                                color: "#0F172A",
                                textTransform: "none",
                                ml: 1,
                            }}
                        >
                            ورود
                        </Button>
                    </Box>
                </Toolbar>
            </Container>
        </AppBar>
    );
};