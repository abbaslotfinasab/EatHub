import {useState} from "react";
import {
    Alert,
    Avatar,
    Box,
    Button,
    Card,
    CardContent,
    Divider,
    Stack,
    TextField,
    Typography,
} from "@mui/material";
import SaveRoundedIcon from "@mui/icons-material/SaveRounded";
import LockResetRoundedIcon from "@mui/icons-material/LockResetRounded";
import PhotoCameraRoundedIcon from "@mui/icons-material/PhotoCameraRounded";
import {apiClient} from "../../data/http/http-client.ts";
import {meMapper} from "../../data/mappers/meMapper.ts";
import {useAuthStore} from "../store/auth.store.ts";
import {useUploadFile} from "../hooks/useUploadFile.ts";
import {useFilePreview} from "../forms/upload/useFilePreview.ts";

const getErrorMessage = (error: unknown, fallback: string) => {
    if (typeof error === "object" && error !== null && "response" in error) {
        const response = (error as {response?: {data?: {detail?: string; name?: string[]; number?: string[]}}}).response;
        return response?.data?.detail
            || response?.data?.name?.[0]
            || response?.data?.number?.[0]
            || fallback;
    }
    return fallback;
};

export const ProfilePage = () => {
    const me = useAuthStore((state) => state.me);
    const setMe = useAuthStore((state) => state.setMe);
    const [name, setName] = useState(me?.name ?? "");
    const [number, setNumber] = useState(me?.number ?? "");
    const [avatarFile, setAvatarFile] = useState<File | null>(null);
    const [savingProfile, setSavingProfile] = useState(false);
    const [profileError, setProfileError] = useState("");
    const [profileSuccess, setProfileSuccess] = useState("");

    const [oldPassword, setOldPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [savingPassword, setSavingPassword] = useState(false);
    const [passwordError, setPasswordError] = useState("");
    const [passwordSuccess, setPasswordSuccess] = useState("");

    const initials = name.trim().charAt(0).toUpperCase() || "U";

    const saveProfile = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setSavingProfile(true);
        setProfileError("");
        setProfileSuccess("");
        try {
            const uploaded = avatarFile
                ? await uploadFile({file: avatarFile, purpose: "avatar"})
                : null;
            const payload = {
                name: name.trim(),
                number: number.trim(),
                ...(uploaded ? {avatar: uploaded.path} : {}),
            };
            const {data} = await apiClient.patch("/accounts/auth/me/", payload);
            setMe(meMapper(data));
            setAvatarFile(null);
            setProfileSuccess("اطلاعات پروفایل با موفقیت ذخیره شد.");
        } catch (error) {
            setProfileError(getErrorMessage(error, "ذخیره اطلاعات پروفایل انجام نشد."));
        } finally {
            setSavingProfile(false);
        }
    };

    const changePassword = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setPasswordError("");
        setPasswordSuccess("");
        if (newPassword !== confirmPassword) {
            setPasswordError("تکرار رمز عبور جدید با آن مطابقت ندارد.");
            return;
        }
        if (newPassword.length < 8) {
            setPasswordError("رمز عبور جدید باید حداقل ۸ کاراکتر باشد.");
            return;
        }

        setSavingPassword(true);
        try {
            await apiClient.post("/accounts/auth/change-password/", {
                old_password: oldPassword,
                new_password: newPassword,
            });
            setOldPassword("");
            setNewPassword("");
            setConfirmPassword("");
            setPasswordSuccess("رمز عبور با موفقیت تغییر کرد.");
        } catch (error) {
            setPasswordError(getErrorMessage(error, "تغییر رمز عبور انجام نشد."));
        } finally {
            setSavingPassword(false);
        }
    };

    return (
        <Box sx={{maxWidth: 920, mx: "auto", direction: "rtl"}}>
            <Stack spacing={1} sx={{mb: 3}}>
                <Typography variant="h4" sx={{fontWeight: 800}}>پروفایل کاربری</Typography>
                <Typography color="text.secondary">
                    اطلاعات حساب و امنیت ورود خود را مدیریت کنید.
                </Typography>
            </Stack>

            <Card elevation={0} sx={{border: "1px solid #E5E7EB", borderRadius: 3, mb: 3}}>
                <CardContent sx={{p: {xs: 2, md: 3}}}>
                    <Typography variant="h6" sx={{fontWeight: 700, mb: 2}}>اطلاعات شخصی</Typography>
                    <Box component="form" onSubmit={saveProfile}>
                        <Stack direction={{xs: "column", sm: "row"}} spacing={3} sx={{mb: 3, alignItems: {sm: "center"}}}>
                            <Avatar src={avatarPreview?.url ?? me?.avatar ?? undefined} sx={{width: 88, height: 88, bgcolor: "#10281A", fontSize: 30}}>
                                {initials}
                            </Avatar>
                            <Box>
                                <Typography sx={{fontWeight: 700}}>{me?.name}</Typography>
                                <Typography variant="body2" color="text.secondary">{me?.email}</Typography>
                                <Button component="label" size="small" startIcon={<PhotoCameraRoundedIcon/>} sx={{mt: 1}}>
                                    تغییر تصویر پروفایل
                                    <input
                                        hidden
                                        type="file"
                                        accept="image/*"
                                        onChange={(event) => setAvatarFile(event.target.files?.[0] ?? null)}
                                    />
                                </Button>
                                {avatarFile && <Typography variant="caption" sx={{display: "block"}}>{avatarFile.name} · {Math.round(avatarFile.size / 1024)} KB</Typography>}
                                {avatarFile && <Typography variant="caption" color="text.secondary">آپلود هنگام ذخیره انجام می‌شود. {uploadProgress > 0 ? `${uploadProgress}%` : ""}</Typography>}
                            </Box>
                        </Stack>

                        {profileError && <Alert severity="error" sx={{mb: 2}}>{profileError}</Alert>}
                        {profileSuccess && <Alert severity="success" sx={{mb: 2}}>{profileSuccess}</Alert>}

                        <Stack spacing={2}>
                            <TextField
                                label="نام و نام خانوادگی"
                                value={name}
                                onChange={(event) => setName(event.target.value)}
                                required
                                fullWidth
                            />
                            <TextField
                                label="شماره تماس"
                                value={number}
                                onChange={(event) => setNumber(event.target.value)}
                                fullWidth
                            />
                            <TextField
                                label="ایمیل"
                                value={me?.email ?? ""}
                                fullWidth
                                disabled
                                helperText="تغییر ایمیل از تنظیمات حساب در حال حاضر پشتیبانی نمی‌شود."
                            />
                            <Box>
                                <Button type="submit" variant="contained" startIcon={<SaveRoundedIcon/>} disabled={savingProfile || !name.trim()}>
                                    {savingProfile ? "در حال ذخیره..." : "ذخیره تغییرات"}
                                </Button>
                            </Box>
                        </Stack>
                    </Box>
                </CardContent>
            </Card>

            <Card elevation={0} sx={{border: "1px solid #E5E7EB", borderRadius: 3}}>
                <CardContent sx={{p: {xs: 2, md: 3}}}>
                    <Stack direction="row" spacing={1} sx={{mb: 2, alignItems: "center"}}>
                        <LockResetRoundedIcon color="action"/>
                        <Typography variant="h6" sx={{fontWeight: 700}}>امنیت حساب</Typography>
                    </Stack>
                    <Divider sx={{mb: 2}}/>
                    <Box component="form" onSubmit={changePassword}>
                        {passwordError && <Alert severity="error" sx={{mb: 2}}>{passwordError}</Alert>}
                        {passwordSuccess && <Alert severity="success" sx={{mb: 2}}>{passwordSuccess}</Alert>}
                        <Stack spacing={2}>
                            <TextField
                                label="رمز عبور فعلی"
                                type="password"
                                value={oldPassword}
                                onChange={(event) => setOldPassword(event.target.value)}
                                required
                                fullWidth
                            />
                            <TextField
                                label="رمز عبور جدید"
                                type="password"
                                value={newPassword}
                                onChange={(event) => setNewPassword(event.target.value)}
                                required
                                slotProps={{htmlInput: {minLength: 8}}}
                                fullWidth
                            />
                            <TextField
                                label="تکرار رمز عبور جدید"
                                type="password"
                                value={confirmPassword}
                                onChange={(event) => setConfirmPassword(event.target.value)}
                                required
                                fullWidth
                            />
                            <Box>
                                <Button type="submit" variant="outlined" disabled={savingPassword || !oldPassword || !newPassword || !confirmPassword}>
                                    {savingPassword ? "در حال تغییر..." : "تغییر رمز عبور"}
                                </Button>
                            </Box>
                        </Stack>
                    </Box>
                </CardContent>
            </Card>
        </Box>
    );
};
