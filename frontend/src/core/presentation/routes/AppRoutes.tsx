import {BrowserRouter, Routes, Route, Navigate} from "react-router-dom";

import {AppLayout} from "../components/layout/AppLayout";
import {DashboardLayout} from "../components/layout/DashboardLayout";


import {HomePage} from "../pages/HomePage";
import {LoginPage} from "../pages/LoginPage";
import {RegisterPage} from "../pages/RegisterPage";

import {ManagerDashboard} from "../pages/ManagerDashboard";
import {IngredientsListPage} from "../pages/IngredientsListPage";

import {CreateIngredientPage} from "../pages/CreateIngredientPage";
import {CreateMaterialPage} from "../pages/CreateMaterialPage";
import {CreateRecipePage} from "../pages/CreateRecipePage";
import {CreatePurchaseOrderPage} from "../pages/CreatePurchaseOrderPage";
import {CreateMenuPage} from "../pages/CreateMenuPage";
import {ProtectedRoute} from "./ProtectedRoute.tsx";
import {PublicRoute} from "./PublicRoute.tsx";
import {CreateBusinessPage} from "../pages/CreateBusinessPage.tsx";
import {MenuPage} from "../pages/MenuPage.tsx";
import {RestaurantMenuPage} from "../pages/RestaurantMenuPage.tsx";

export const AppRoutes = () => {
    return (
        <BrowserRouter>
            <Routes>

                <Route element={<AppLayout/>}>

                    <Route path="/" element={<HomePage/>}/>
                    <Route path="/home" element={<Navigate to="/" replace/>}/>

                    <Route path="/products/:restaurantSlug/menu" element={<RestaurantMenuPage/>}/>

                </Route>


                {/* PUBLIC */}
                <Route element={<PublicRoute/>}>
                    <Route element={<AppLayout/>}>
                        <Route path="/login" element={<LoginPage/>}/>
                        <Route path="/register" element={<RegisterPage/>}/>
                    </Route>
                </Route>

                {/* PROTECTED */}
                <Route element={<ProtectedRoute/>}>
                    <Route element={<DashboardLayout/>}>
                        <Route path="/business" element={<CreateBusinessPage/>}/>
                        <Route path="/dashboard" element={<ManagerDashboard/>}/>

                        <Route path="/ingredients" element={<IngredientsListPage/>}/>
                        <Route path="/ingredients/create" element={<CreateIngredientPage/>}/>

                        <Route path="/menus" element={<MenuPage/>}/>
                        <Route path="/menus/create" element={<CreateMenuPage/>}/>

                        <Route path="/orders" element={<IngredientsListPage/>}/>
                        <Route path="/orders/create" element={<IngredientsListPage/>}/>

                        <Route path="/materials/create" element={<CreateMaterialPage/>}/>
                        <Route path="/recipes/create" element={<CreateRecipePage/>}/>
                        <Route path="/factor/create" element={<CreatePurchaseOrderPage/>}/>

                    </Route>
                </Route>

            </Routes>
        </BrowserRouter>
    );
};