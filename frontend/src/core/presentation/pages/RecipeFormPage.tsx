import { isAxiosError } from "axios";
import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Box, Button, CircularProgress, Container, Paper, Stack, Typography } from "@mui/material";
import { ArrowBigLeft, Package, Save } from "lucide-react";
import { useEffect } from "react";
import { FormProvider, useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { useCreateRecipe } from "../hooks/useCreateRecipe";
import { useGetRecipe } from "../hooks/useGetRecipe";
import { useUpdateRecipe } from "../hooks/useUpdateRecipe";
import { IngredientList } from "../components/form/IngredientList";
import { FormInput } from "../components/form/FormInput";
import { FormTextarea } from "../components/form/FormTextarea";
import { RecipeFormSchema, type RecipeFormInput, type RecipeFormValues } from "../../domain/use-cases/product/recipe/RecipeFormSchema";
import { useNavbar } from "../hooks/useNavbar";

interface RecipeFormPageProps {
    edit?: boolean;
}

const apiErrorMessage = (error: unknown): string => {
    if (!isAxiosError(error)) return "ذخیره رسپی انجام نشد. دوباره تلاش کنید.";
    const status = error.response?.status;
    if (status === 403) return "شما اجازه مشاهده، ایجاد یا ویرایش رسپی را ندارید.";
    if (status === 404) return "رسپی یا یکی از اقلام انتخاب‌شده پیدا نشد.";
    if (status === 400) {
        const detail = JSON.stringify(error.response?.data ?? "");
        if (detail.includes("Inactive ingredients")) return "مواد اولیه غیرفعال قابل انتخاب نیستند.";
        if (detail.includes("Cannot convert")) return "واحد انتخاب‌شده با واحد ماده اولیه سازگار نیست.";
        if (detail.includes("only once")) return "هر قلم را در هر بخش فقط یک‌بار انتخاب کنید.";
        if (detail.includes("at most one primary output")) return "حداکثر یک محصول خروجی را به‌عنوان محصول اصلی انتخاب کنید.";
        if (detail.includes("greater than or equal to 0")) return "مقدار نمی‌تواند منفی باشد.";
        if (detail.includes("decimal places")) return "مقدار حداکثر ۱۲ رقم اعشار داشته باشد.";
        return "اطلاعات رسپی معتبر نیست. نام، مقدارها، واحدها و مواد انتخاب‌شده را بررسی کنید.";
    }
    return "ارتباط با سرور ناموفق بود. اتصال را بررسی و دوباره تلاش کنید.";
};

export const RecipeFormPage = ({ edit = false }: RecipeFormPageProps) => {
    const navigate = useNavigate();
    const { id: routeId = "" } = useParams<{ id: string }>();
    const recipeId = edit ? routeId : "";
    const recipeQuery = useGetRecipe(recipeId);
    const createMutation = useCreateRecipe();
    const updateMutation = useUpdateRecipe();
    const isSaving = createMutation.isPending || updateMutation.isPending;
    const methods = useForm<RecipeFormInput, unknown, RecipeFormValues>({
        resolver: zodResolver(RecipeFormSchema),
        defaultValues: { name: "", description: "", ingredients: [], outputs: [] },
    });
    const { setRightElement, setShowMenu } = useNavbar();

    useEffect(() => {
        setShowMenu(false);
        setRightElement(
            <button
                type="button"
                onClick={() => navigate("/recipes")}
                className="rounded-lg bg-gray-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-gray-700"
            >
                <ArrowBigLeft className="ml-1 inline h-4 w-4" />
                انصراف
            </button>,
        );
        return () => {
            setRightElement(null);
            setShowMenu(false);
        };
    }, [navigate, setRightElement, setShowMenu]);

    useEffect(() => {
        const recipe = recipeQuery.data;
        if (!recipe || methods.formState.isDirty) return;
        methods.reset({
            name: recipe.recipe.name ?? "",
            description: recipe.recipe.description ?? "",
            ingredients: recipe.ingredients.map((line) => ({
                ingredientId: line.ingredientId ?? "",
                ingredientName: line.ingredientName,
                quantity: String(line.quantity),
                unit: line.unit as RecipeFormInput["ingredients"][number]["unit"],
                notes: line.notes,
            })),
            outputs: recipe.outputs.map((line) => ({
                ingredientId: line.ingredientId ?? "",
                ingredientName: line.ingredientName,
                quantity: String(line.quantity),
                unit: line.unit as RecipeFormInput["outputs"][number]["unit"],
                isPrimary: line.isPrimary ?? false,
                notes: line.notes,
            })),
        });
    }, [methods, methods.formState.isDirty, recipeQuery.data]);

    const onSubmit = async (values: RecipeFormValues) => {
        if (isSaving) return;
        createMutation.reset();
        updateMutation.reset();
        try {
            if (edit) {
                await updateMutation.mutateAsync({ id: recipeId, values });
            } else {
                await createMutation.mutateAsync(values);
            }
            navigate("/recipes");
        } catch {
            // The mutation state is rendered below with a Persian error message.
        }
    };

    const saveError = edit ? updateMutation.error : createMutation.error;
    const validationErrors = methods.formState.errors;

    if (edit && recipeQuery.isLoading) {
        return <Container dir="rtl" sx={{ py: 8, display: "flex", justifyContent: "center" }}><CircularProgress /></Container>;
    }
    if (edit && recipeQuery.isError) {
        return <Container dir="rtl" sx={{ py: 3 }}><Alert severity="error">{apiErrorMessage(recipeQuery.error)}</Alert></Container>;
    }
    if (edit && recipeQuery.data === null) {
        return <Container dir="rtl" sx={{ py: 3 }}><Alert severity="warning">رسپی موردنظر پیدا نشد.</Alert><Button sx={{ mt: 2 }} onClick={() => navigate("/recipes")}>بازگشت به رسپی‌ها</Button></Container>;
    }

    return (
        <FormProvider {...methods}>
            <Container maxWidth="md" dir="rtl" sx={{ py: 3 }}>
                <Paper component="form" onSubmit={methods.handleSubmit(onSubmit)} sx={{ p: { xs: 2, sm: 4 } }}>
                    <Stack spacing={3}>
                        <Typography variant="h4" component="h1" sx={{ fontWeight: 700 }}>{edit ? "ویرایش رسپی" : "رسپی جدید"}</Typography>
                        {saveError && <Alert severity="error">{apiErrorMessage(saveError)}</Alert>}
                        {validationErrors.ingredients?.message && <Alert severity="warning">{validationErrors.ingredients.message}</Alert>}
                        {validationErrors.outputs?.message && <Alert severity="warning">{validationErrors.outputs.message}</Alert>}

                        <section className="space-y-4">
                            <div className="flex items-center gap-2"><Package className="h-5 w-5 text-rose-600" /><Typography variant="h6">اطلاعات پایه</Typography></div>
                            <FormInput name="name" label="نام رسپی *" />
                            <FormTextarea name="description" label="توضیحات" rows={3} />
                        </section>

                        <section className="space-y-4">
                            <IngredientList fieldName="ingredients" heading="مواد مصرفی" quantityAsText preventDuplicates />
                        </section>
                        <section className="space-y-4">
                            <IngredientList fieldName="outputs" heading="محصولات خروجی" outputMode quantityAsText preventDuplicates />
                            <Typography variant="caption" color="text.secondary">
                                حداکثر یک خروجی می‌تواند محصول اصلی باشد؛ انتخاب محصول اصلی اختیاری است.
                            </Typography>
                        </section>

                        <Box sx={{ display: "flex", gap: 1, justifyContent: "flex-start" }}>
                            <Button type="button" variant="outlined" disabled={isSaving} onClick={() => navigate("/recipes")}>انصراف</Button>
                            <Button type="submit" variant="contained" disabled={isSaving} startIcon={isSaving ? <CircularProgress size={16} color="inherit" /> : <Save size={16} />}>
                                {isSaving ? "در حال ذخیره..." : "ذخیره"}
                            </Button>
                        </Box>
                    </Stack>
                </Paper>
            </Container>
        </FormProvider>
    );
};
