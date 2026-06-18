import { Box } from "@mui/material";
import { useState } from "react";

import { EmailField } from "./EmailField";
import { PasswordField } from "./PasswordField";
import { ForgotPasswordLink } from "./ForgotPasswordLink";
import { LoginButton } from "./LoginButton";
import { RegisterLink } from "./RegisterLink";

import { useLogin } from "../../hooks/useLogin";

import { useNavigate } from "react-router-dom";


export const LoginForm = () => {
    const login = useLogin();
    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            await login(email, password);

            navigate("/dashboard"); // ✅ اینجا حالا درست کار می‌کنه
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <Box
            component="form"
            onSubmit={handleSubmit}
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 3,
            }}
        >
            <EmailField value={email} onChange={setEmail} />

            <PasswordField value={password} onChange={setPassword} />

            <ForgotPasswordLink />

            <LoginButton />

            <RegisterLink />
        </Box>
    );
};