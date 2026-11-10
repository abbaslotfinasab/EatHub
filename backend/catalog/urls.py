from django.urls import path

from catalog.presentation.views import ProductDetailAPIView, ProductListCreateAPIView


app_name = "catalog"

urlpatterns = [
    path("products/", ProductListCreateAPIView.as_view(), name="product-list-create"),
    path("products/<int:pk>/", ProductDetailAPIView.as_view(), name="product-detail"),
]
