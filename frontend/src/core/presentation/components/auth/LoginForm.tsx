import { Box } from "@mui/material";
import { useState } from "react";

import {IdentifierField} from "./IdentifierField.tsx";
import { PasswordField } from "./PasswordField";
import { ForgotPasswordLink } from "./ForgotPasswordLink";
import { LoginButton } from "./LoginButton";
import { RegisterLink } from "./RegisterLink";

import { useLogin } from "../../hooks/useLogin";

import { useNavigate } from "react-router-dom";
import {useAuthStore} from "../../store/auth.store.ts";


export const LoginForm = () => {
    const login = useLogin();
    const navigate = useNavigate();

    const [identifier, setidentifier] = useState("");
    const [password, setPassword] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            await login(identifier, password);

            console.log("AFTER LOGIN", useAuthStore.getState());

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
            <IdentifierField value={identifier} onChange={setidentifier} />

            <PasswordField value={password} onChange={setPassword} />

            <ForgotPasswordLink />

            <LoginButton />

            <RegisterLink />
        </Box>
    );
};