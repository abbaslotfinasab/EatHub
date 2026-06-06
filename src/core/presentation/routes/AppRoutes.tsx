// src/presentation/routes/AppRoutes.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { CreateRecipePage } from '../pages/CreateRecipePage';
import { Layout } from "../components/layout/Layout";
import {CreateIngredientPage} from "../pages/CreateIngredientPage.tsx";
import {CreateMaterialPage} from "../pages/CreateMaterialPage.tsx";
import {CreatePurchaseOrderPage} from "../pages/CreatePurchaseOrderPage.tsx";
import {CreateMenuPage} from "../pages/CreateMenuPage.tsx";
import {IngredientsListPage} from "../pages/IngredientsListPage.tsx";
import {MaterialsListPage} from "../pages/MaterialsListPage.tsx";
import {RecipeListPage} from "../pages/RecipeListPage.tsx";
import { ManagerDashboard } from "../pages/ManagerDashboard";

export const AppRoutes = () => {
    return (
        <BrowserRouter>
            <Routes>   {/* ✅ اضافه کردن Routes */}
                <Route path="/" element={<Layout />}>
                    <Route path="ingredients/create" element={<CreateIngredientPage />} />
                    <Route path="materials/create" element={<CreateMaterialPage />} />
                    <Route path="recipes/create" element={<CreateRecipePage />} />
                    <Route path="factor/create" element={<CreatePurchaseOrderPage />} />
                    <Route path="menus/create" element={<CreateMenuPage />} />
                    <Route path="ingredients" element={<IngredientsListPage />} />
                    <Route path="materials" element={<MaterialsListPage />} />
                    <Route path="recipes" element={<RecipeListPage />} />
                    <Route path="dashboard" element={<ManagerDashboard />} />






                    {/* مسیرهای دیگر */}
                </Route>
            </Routes>
        </BrowserRouter>
    );
};