from django.urls import path

from inventory.views import StockBalanceListAPIView
from inventory.presentation.master_data_views import (
    ItemDetailAPIView,
    ItemListCreateAPIView,
    WarehouseDetailAPIView,
    WarehouseListCreateAPIView,
)
from inventory.presentation.operation_views import (
    IssueDetailAPIView, IssueListCreateAPIView, MovementHistoryAPIView,
    OpeningStockCreateAPIView, OpeningStockDetailAPIView,
    StocktakeDetailAPIView, StocktakeListCreateAPIView,
    TransferDetailAPIView, TransferListCreateAPIView,
)
from inventory.presentation.recipe_views import (
    RecipeDetailAPIView,
    RecipeInputCollectionAPIView,
    RecipeInputDetailAPIView,
    RecipeListCreateAPIView,
    RecipeOutputCollectionAPIView,
    RecipeOutputDetailAPIView,
)
from inventory.presentation.compound_material_views import (
    CompoundMaterialDetailAPIView,
    CompoundMaterialListCreateAPIView,
)
from inventory.presentation.reservation_views import (
    ReservationAvailabilityAPIView,
    ReservationDetailAPIView,
    ReservationListCreateAPIView,
)


app_name = 'inventory'


urlpatterns = [
    path("balances/", StockBalanceListAPIView.as_view(), name="stock-balances"),
    path("items/", ItemListCreateAPIView.as_view(), name="item-list-create"),
    path("items/<int:pk>/", ItemDetailAPIView.as_view(), name="item-detail"),
    path("compound-materials/", CompoundMaterialListCreateAPIView.as_view(), name="compound-material-list-create"),
    path("compound-materials/<int:pk>/", CompoundMaterialDetailAPIView.as_view(), name="compound-material-detail"),
    path("warehouses/", WarehouseListCreateAPIView.as_view(), name="warehouse-list-create"),
    path("warehouses/<int:pk>/", WarehouseDetailAPIView.as_view(), name="warehouse-detail"),
    path("issues/", IssueListCreateAPIView.as_view(), name="issue-list-create"),
    path("issues/<int:pk>/", IssueDetailAPIView.as_view(), name="issue-detail"),
    path("issues/<int:pk>/<str:action>/", IssueDetailAPIView.as_view(), name="issue-action"),
    path("transfers/", TransferListCreateAPIView.as_view(), name="transfer-list-create"),
    path("transfers/<int:pk>/", TransferDetailAPIView.as_view(), name="transfer-detail"),
    path("transfers/<int:pk>/<str:action>/", TransferDetailAPIView.as_view(), name="transfer-action"),
    path("stocktakes/", StocktakeListCreateAPIView.as_view(), name="stocktake-list-create"),
    path("stocktakes/<int:pk>/", StocktakeDetailAPIView.as_view(), name="stocktake-detail"),
    path("stocktakes/<int:pk>/<str:action>/", StocktakeDetailAPIView.as_view(), name="stocktake-action"),
    path("movements/", MovementHistoryAPIView.as_view(), name="movement-history"),
    path("reservations/", ReservationListCreateAPIView.as_view(), name="reservation-list-create"),
    path("reservations/availability/", ReservationAvailabilityAPIView.as_view(), name="reservation-availability"),
    path("reservations/<int:pk>/", ReservationDetailAPIView.as_view(), name="reservation-detail"),
    path("reservations/<int:pk>/<str:action>/", ReservationDetailAPIView.as_view(), name="reservation-action"),
    path("opening-stock/", OpeningStockCreateAPIView.as_view(), name="opening-stock-create"),
    path("opening-stock/<int:pk>/", OpeningStockDetailAPIView.as_view(), name="opening-stock-detail"),
    path("recipes/", RecipeListCreateAPIView.as_view(), name="recipe-list-create"),
    path("recipes/<int:pk>/", RecipeDetailAPIView.as_view(), name="recipe-detail"),
    path("recipes/<int:recipe_id>/inputs/", RecipeInputCollectionAPIView.as_view(), name="recipe-input-list-create"),
    path("recipes/<int:recipe_id>/inputs/<int:line_id>/", RecipeInputDetailAPIView.as_view(), name="recipe-input-detail"),
    path("recipes/<int:recipe_id>/outputs/", RecipeOutputCollectionAPIView.as_view(), name="recipe-output-list-create"),
    path("recipes/<int:recipe_id>/outputs/<int:line_id>/", RecipeOutputDetailAPIView.as_view(), name="recipe-output-detail"),
]
