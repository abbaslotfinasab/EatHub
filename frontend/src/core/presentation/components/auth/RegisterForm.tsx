import { Box } from "@mui/material";
import { useState } from "react";

import { FullNameField } from "./FullNameField";
import { EmailField } from "./EmailField.tsx";
import { PhoneField } from "./PhoneField";
import { PasswordField } from "./PasswordField";
import { ConfirmPasswordField } from "./ConfirmPasswordField";
import { RegisterButton } from "./RegisterButton";
import { LoginLink } from "./LoginLink";

import { useRegister } from "../../hooks/useRegister";
import {useNavigate} from "react-router-dom";

export const RegisterForm = () => {
    const { register } = useRegister();
    const navigate = useNavigate();


    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [number, setNumber] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] =
        useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (password !== confirmPassword) {
            alert("Passwords do not match");
            return;
        }

        try {
            await register(email, password, name, number);

            navigate("/business"); // ✅ اینجا حالا درست کار می‌کنه
        } catch (err) {
            console.error("REGISTER FAILED:", err);
        }
    };

    return (
        <Box component="form" onSubmit={handleSubmit}>
            <FullNameField value={name} onChange={setName} />
            <EmailField value={email} onChange={setEmail} />
            <PhoneField value={number} onChange={setNumber} />
            <PasswordField value={password} onChange={setPassword} />
            <ConfirmPasswordField
                value={confirmPassword}
                onChange={setConfirmPassword}
            />
            <RegisterButton loading={false} />
            <LoginLink />
        </Box>
    );
};