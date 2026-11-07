import {BrowserRouter, Routes, Route, Navigate} from "react-router-dom";
import {AppLayout} from "../components/layout/AppLayout";
import {DashboardLayout} from "../components/layout/DashboardLayout";
import {HomePage} from "../pages/HomePage";
import {LoginPage} from "../pages/LoginPage";
import {RegisterPage} from "../pages/RegisterPage";
import {ManagerDashboard} from "../pages/ManagerDashboard";
import {IngredientsListPage} from "../pages/IngredientsListPage";
import {CreateIngredientPage} from "../pages/CreateIngredientPage";
import {CompoundMaterialFormPage, CompoundMaterialsPage} from "../pages/CompoundMaterialsPage";
import {CreateRecipePage} from "../pages/CreateRecipePage";
import {EditRecipePage} from "../pages/EditRecipePage";
import {CreateMenuPage} from "../pages/menu/CreateMenuPage.tsx";
import {CreateBusinessPage} from "../pages/CreateBusinessPage.tsx";
import {MenuPage} from "../pages/menu/MenuPage.tsx";
import {PublicMenuPage} from "../pages/menu/PublicMenuPage.tsx";
import {AuthGuard} from "./AuthGuarad.tsx";
import {GuestGuard} from "./GuestGuard.tsx";
import {BusinessGuard} from "./BusinessGuard.tsx";
import {EditMenuPage} from "../pages/menu/EditMenuPage.tsx";
import {EditMenuItemPage} from "../pages/menu/EditMenuItemPage.tsx";
import {OrdersPage} from "../pages/order/OrdersPage.tsx";
import {CreateOrderPage} from "../pages/order/CreateOrderPage.tsx";
import {UpdateOrderPage} from "../pages/order/UpdateOrderPage.tsx";
import {CustomersPage} from "../pages/customer/CustomersPage.tsx";
import {InventoryBalancesPage} from "../pages/InventoryBalancesPage.tsx";
import {RecipeListPage} from "../pages/RecipeListPage.tsx";
import {OpeningStockPage} from "../pages/OpeningStockPage.tsx";
import {PurchaseOrdersPage} from "../pages/purchase/PurchaseOrdersPage.tsx";
import {GoodsReceivingPage} from "../pages/purchase/GoodsReceivingPage.tsx";
import {CreatePurchaseOrderPage} from "../pages/purchase/CreatePurchaseOrderPage.tsx";
import {PurchaseOrderDetailPage} from "../pages/purchase/PurchaseOrderDetailPage.tsx";
import {InventorySettingsPage} from "../pages/InventorySettingsPage.tsx";
import {ProfilePage} from "../pages/ProfilePage.tsx";

export const AppRoutes = () => (
    <BrowserRouter>
        <Routes>
            <Route element={<AppLayout/>}>
                <Route path="/" element={<HomePage/>}/>
                <Route path="/products/:slug/menu" element={<PublicMenuPage/>}/>
            </Route>

            <Route element={<GuestGuard/>}>
                <Route element={<AppLayout/>}>
                    <Route path="/login" element={<LoginPage/>}/>
                    <Route path="/register" element={<RegisterPage/>}/>
                </Route>
            </Route>

            <Route element={<AuthGuard/>}>
                <Route element={<DashboardLayout/>}>
                    <Route path="/business" element={<CreateBusinessPage/>}/>
                    <Route path="/profile" element={<ProfilePage/>}/>

                    <Route element={<BusinessGuard/>}>
                        <Route path="/dashboard" element={<ManagerDashboard/>}/>
                        <Route path="/settings/inventory" element={<InventorySettingsPage/>}/>
                        <Route path="/ingredients" element={<IngredientsListPage/>}/>
                        <Route path="/inventory" element={<InventoryBalancesPage/>}/>
                        <Route path="/inventory/opening-stock" element={<OpeningStockPage/>}/>
                        <Route path="/ingredients/create" element={<CreateIngredientPage/>}/>
                        <Route path="/ingredients/:id/edit" element={<CreateIngredientPage/>}/>
                        <Route path="/materials" element={<CompoundMaterialsPage/>}/>
                        <Route path="/materials/create" element={<CompoundMaterialFormPage/>}/>
                        <Route path="/materials/:id/edit" element={<CompoundMaterialFormPage/>}/>
                        <Route path="/warehouses" element={<Navigate to="/settings/inventory" replace/>}/>
                        <Route path="/inventory/operations" element={<Navigate to="/inventory?view=operations" replace/>}/>
                        <Route path="/recipes" element={<RecipeListPage/>}/>
                        <Route path="/purchase/orders" element={<PurchaseOrdersPage/>}/>
                        <Route path="/purchase/orders/create" element={<CreatePurchaseOrderPage/>}/>
                        <Route path="/purchase/orders/:id/edit" element={<CreatePurchaseOrderPage/>}/>
                        <Route path="/purchase/orders/:id/receive" element={<GoodsReceivingPage/>}/>
                        <Route path="/purchase/orders/:id" element={<PurchaseOrderDetailPage/>}/>
                        <Route path="/menus" element={<MenuPage/>}/>
                        <Route path="/menus/create" element={<CreateMenuPage/>}/>
                        <Route path="/menus/:id/edit" element={<EditMenuPage/>}/>
                        <Route path="/menu-items/:id/edit" element={<EditMenuItemPage/>}/>
                        <Route path="/orders" element={<OrdersPage/>}/>
                        <Route path="/orders/create" element={<CreateOrderPage/>}/>
                        <Route path="/orders/:id/edit" element={<UpdateOrderPage/>}/>
                        <Route path="/recipes/create" element={<CreateRecipePage/>}/>
                        <Route path="/recipes/:id/edit" element={<EditRecipePage/>}/>
                        <Route path="/customers/" element={<CustomersPage/>}/>
                    </Route>
                </Route>
            </Route>
        </Routes>
    </BrowserRouter>
);
