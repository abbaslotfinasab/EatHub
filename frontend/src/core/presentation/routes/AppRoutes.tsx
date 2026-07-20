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
import {CreateMenuPage} from "../pages/menu/CreateMenuPage.tsx";
import {CreateBusinessPage} from "../pages/CreateBusinessPage.tsx";
import {MenuPage} from "../pages/menu/MenuPage.tsx";
import {PublicMenuPage} from "../pages/menu/PublicMenuPage.tsx";
import {AuthGuard} from "./AuthGuarad.tsx";
import {GuestGuard} from "./GuestGuard.tsx";
import {BusinessGuard} from "./BusinessGuard.tsx";
import {EditMenuPage} from "../pages/menu/EditMenuPage.tsx";
import {OrdersPage} from "../pages/order/OrdersPage.tsx";
import {CreateOrderPage} from "../pages/order/CreateOrderPage.tsx";
import {UpdateOrderPage} from "../pages/order/UpdateOrderPage.tsx";
import {CustomersPage} from "../pages/customer/CustomersPage.tsx";

export const AppRoutes = () => {
    return (
        <BrowserRouter>
            <Routes>

                {/* 🌍 PUBLIC (no auth) */}
                <Route element={<AppLayout/>}>
                    <Route path="/" element={<HomePage/>}/>
                    <Route path="/products/:slug/menu" element={<PublicMenuPage/>}/>
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

                        <Route element={<BusinessGuard/>}>


                            <Route path="/dashboard" element={<ManagerDashboard/>}/>

                            <Route path="/ingredients" element={<IngredientsListPage/>}/>
                            <Route path="/ingredients/create" element={<CreateIngredientPage/>}/>

                            <Route path="/menus" element={<MenuPage/>}/>
                            <Route path="/menus/create" element={<CreateMenuPage/>}/>
                            <Route path="/menus/:id/edit" element={<EditMenuPage/>}/>


                            <Route path="/orders" element={<OrdersPage/>}/>
                            <Route path="/orders/create" element={<CreateOrderPage/>}/>
                            <Route path="/orders/:id/edit" element={<UpdateOrderPage/>}/>


                            <Route path="/materials/create" element={<CreateMaterialPage/>}/>
                            <Route path="/recipes/create" element={<CreateRecipePage/>}/>

                            <Route path="/customers/" element={<CustomersPage/>}/>

                        </Route>

                    </Route>
                </Route>

            </Routes>
        </BrowserRouter>
    );
};