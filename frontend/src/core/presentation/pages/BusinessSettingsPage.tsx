import {useEffect, useState} from "react";
import {Alert, Avatar, Box, Button, Card, CardContent, CircularProgress, Stack, TextField, Typography} from "@mui/material";
import PhotoCameraRoundedIcon from "@mui/icons-material/PhotoCameraRounded";
import SaveRoundedIcon from "@mui/icons-material/SaveRounded";
import {apiClient} from "../../data/http/http-client.ts";
import {useUploadFile} from "../hooks/useUploadFile.ts";
import {useFilePreview} from "../forms/upload/useFilePreview.ts";
import {meMapper} from "../../data/mappers/meMapper.ts";
import {useAuthStore} from "../store/auth.store.ts";

interface BusinessProfile {
    name: string;
    number: string;
    address: string;
    logo: string | null;
}

export const BusinessSettingsSection = ({embedded = false}: {embedded?: boolean}) => {
    const setMe = useAuthStore((state) => state.setMe);
    const [profile, setProfile] = useState<BusinessProfile>({name: "", number: "", address: "", logo: null});
    const [logoFile, setLogoFile] = useState<File | null>(null);
    const [removeLogo, setRemoveLogo] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const {mutateAsync: uploadFile, progress} = useUploadFile();
    const preview = useFilePreview(logoFile, removeLogo ? null : profile.logo);

    useEffect(() => {
        let active = true;
        apiClient.get<BusinessProfile>("/accounts/business/profile/")
            .then(({data}) => { if (active) setProfile(data); })
            .catch(() => { if (active) setError("دریافت اطلاعات کسب‌وکار انجام نشد."); })
            .finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
    }, []);

    const save = async (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setSaving(true);
        setError("");
        setSuccess("");
        try {
            const uploaded = logoFile
                ? await uploadFile({file: logoFile, purpose: "business_logo"})
                : null;
            const payload = {
                name: profile.name.trim(),
                number: profile.number.trim(),
                address: profile.address.trim(),
                ...(uploaded ? {logo: uploaded.path} : removeLogo ? {logo: null} : {}),
            };
            const {data} = await apiClient.patch<BusinessProfile>("/accounts/business/profile/", payload);
            setProfile(data);
            const {data: meData} = await apiClient.get("/accounts/auth/me/");
            setMe(meMapper(meData));
            setLogoFile(null);
            setRemoveLogo(false);
            setSuccess("اطلاعات کسب‌وکار با موفقیت ذخیره شد.");
        } catch {
            setError("ذخیره اطلاعات کسب‌وکار انجام نشد. دوباره تلاش کنید.");
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <Box sx={{display: "flex", justifyContent: "center", p: 6}}><CircularProgress/></Box>;

    return (
        <Box sx={{maxWidth: 900, mx: "auto", direction: "rtl"}}>
            {!embedded && <Stack spacing={1} sx={{mb: 3}}>
                <Typography variant="h4" sx={{fontWeight: 800}}>اطلاعات کسب‌وکار</Typography>
                <Typography color="text.secondary">نام، اطلاعات تماس و لوگوی کسب‌وکار فعال را مدیریت کنید.</Typography>
            </Stack>}
            {embedded && <Typography variant="h6" sx={{fontWeight: 700, mb: 2}}>اطلاعات کسب‌وکار</Typography>}
            <Card elevation={0} sx={{border: "1px solid #E5E7EB", borderRadius: 3}}>
                <CardContent sx={{p: {xs: 2, md: 3}}}>
                    {error && <Alert severity="error" sx={{mb: 2}}>{error}</Alert>}
                    {success && <Alert severity="success" sx={{mb: 2}}>{success}</Alert>}
                    <Box component="form" onSubmit={save}>
                        <Stack spacing={3}>
                            <Stack direction={{xs: "column", sm: "row"}} spacing={2} sx={{alignItems: "center"}}>
                                <Avatar variant="rounded" src={preview?.url ?? undefined} sx={{width: 112, height: 112, bgcolor: "grey.100", border: "1px dashed", borderColor: "divider"}}/>
                                <Stack spacing={1}>
                                    <Typography sx={{fontWeight: 700}}>لوگوی کسب‌وکار</Typography>
                                    <Typography variant="body2" color="text.secondary">فرمت‌های JPG، PNG و WEBP · حداکثر ۵ مگابایت</Typography>
                                    <Stack direction="row" spacing={1}>
                                        <Button component="label" variant="outlined" size="small" startIcon={<PhotoCameraRoundedIcon/>}>
                                            {profile.logo || logoFile ? "تغییر لوگو" : "انتخاب لوگو"}
                                            <input hidden type="file" accept="image/jpeg,image/png,image/webp" onChange={event => {setLogoFile(event.target.files?.[0] ?? null); setRemoveLogo(false);}}/>
                                        </Button>
                                        {(profile.logo || logoFile) && <Button color="error" size="small" onClick={() => {setLogoFile(null); setRemoveLogo(true);}}>حذف لوگو</Button>}
                                    </Stack>
                                    {saving && logoFile && <Typography variant="caption" color="text.secondary">در حال آپلود: {progress}%</Typography>}
                                </Stack>
                            </Stack>
                            <TextField label="نام کسب‌وکار" value={profile.name} onChange={e => setProfile(p => ({...p, name: e.target.value}))} required fullWidth/>
                            <TextField label="شماره تماس" value={profile.number} onChange={e => setProfile(p => ({...p, number: e.target.value}))} fullWidth/>
                            <TextField label="آدرس" value={profile.address} onChange={e => setProfile(p => ({...p, address: e.target.value}))} multiline minRows={2} fullWidth/>
                            <Box><Button type="submit" variant="contained" startIcon={<SaveRoundedIcon/>} disabled={saving || !profile.name.trim()}>{saving ? "در حال ذخیره…" : "ذخیره تغییرات"}</Button></Box>
                        </Stack>
                    </Box>
                </CardContent>
            </Card>
        </Box>
    );
};
