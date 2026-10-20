from django.urls import path

from inventory.views import StockBalanceListAPIView


app_name = 'inventory'


urlpatterns = [
    path("balances/", StockBalanceListAPIView.as_view(), name="stock-balances"),
]
