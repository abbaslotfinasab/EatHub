import {BrowserRouter, Routes, Route} from "react-router-dom";

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
import {CreateBusinessPage} from "../pages/CreateBusinessPage.tsx";
import {MenuPage} from "../pages/MenuPage.tsx";
import {RestaurantMenuPage} from "../pages/RestaurantMenuPage.tsx";
import { AuthGuard } from "./AuthGuarad.tsx";
import {GuestGuard} from "./GuestGuard.tsx";

export const AppRoutes = () => {
    return (
        <BrowserRouter>
            <Routes>

                {/* 🌍 PUBLIC (no auth) */}
                <Route element={<AppLayout/>}>
                    <Route path="/" element={<HomePage/>}/>
                    <Route path="/products/:slug/menu" element={<RestaurantMenuPage/>}/>
                </Route>

                {/* 🔑 GUEST ONLY */}
                <Route element={<GuestGuard/>}>
                    <Route element={<AppLayout/>}>
                        <Route path="/login" element={<LoginPage/>}/>
                        <Route path="/register" element={<RegisterPage/>}/>
                    </Route>
                </Route>

                {/* 🔴 PROTECTED APP */}
                <Route element={<AuthGuard/>}>
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