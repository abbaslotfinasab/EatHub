from django.db import IntegrityError
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.views import TenantAPIView
from core.enums import PermissionCode
from inventory.application.use_cases.manage_recipes import (
    InactiveRecipeIngredient,
    ManageRecipes,
    RecipeIngredientNotFound,
    RecipeLineCommand,
    RecipeNotFound,
)
from inventory.domain.exceptions import InventoryDomainError
from inventory.infrastructure.django.recipe_repository import DjangoRecipeRepository
from inventory.infrastructure.django.unit_of_work import DjangoInventoryUnitOfWork
from inventory.presentation.serializers.recipe import (
    RecipeCreateSerializer,
    RecipeInputPatchSerializer,
    RecipeOutputPatchSerializer,
    RecipeOutputWriteSerializer,
    RecipePageSerializer,
    RecipeQuerySerializer,
    RecipeSerializer,
    RecipeUpdateSerializer,
    RecipeLineWriteSerializer,
)


def _use_case() -> ManageRecipes:
    return ManageRecipes(DjangoRecipeRepository(), DjangoInventoryUnitOfWork())


def _permission(request, code: PermissionCode) -> None:
    if code.value not in request.permissions:
        raise PermissionDenied("You do not have permission to manage Recipes.")


def _run(call):
    try:
        return call()
    except RecipeNotFound as error:
        raise NotFound(str(error)) from error
    except RecipeIngredientNotFound as error:
        raise NotFound(str(error)) from error
    except InactiveRecipeIngredient as error:
        raise serializers.ValidationError({"ingredient_id": str(error)}) from error
    except IntegrityError as error:
        raise serializers.ValidationError({
            "detail": "A recipe line conflicts with an existing line or database constraint."
        }) from error
    except (InventoryDomainError, ValueError) as error:
        raise serializers.ValidationError({"detail": str(error)}) from error


def _line_command(data: dict, *, output: bool = False) -> RecipeLineCommand:
    return RecipeLineCommand(
        ingredient_id=data["ingredient_id"],
        quantity=data["quantity"],
        unit=data["unit"],
        notes=data.get("notes"),
        is_primary=data.get("is_primary", False) if output else False,
    )


class RecipeListCreateAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _permission(request, PermissionCode.INVENTORY_VIEW)
        query = RecipeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        values = query.validated_data
        page = _run(lambda: _use_case().list(
            request.business.id,
            page=values["page"],
            page_size=values["page_size"],
            search=values.get("search"),
            recipe_type=values.get("type"),
            is_active=values.get("is_active"),
        ))
        return Response(RecipePageSerializer(page).data)

    def post(self, request):
        _permission(request, PermissionCode.INVENTORY_RECIPE_MANAGE)
        serializer = RecipeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        recipe = _run(lambda: _use_case().create(
            request.business.id,
            name=values["name"],
            recipe_type=values["type"],
            code=values.get("code"),
            description=values.get("description"),
            is_active=values["is_active"],
            inputs=[_line_command(row) for row in values["inputs"]],
            outputs=[_line_command(row, output=True) for row in values["outputs"]],
        ))
        return Response(RecipeSerializer(recipe).data, status=status.HTTP_201_CREATED)


class RecipeDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        _permission(request, PermissionCode.INVENTORY_VIEW)
        recipe = _run(lambda: _use_case().get(request.business.id, pk))
        return Response(RecipeSerializer(recipe).data)

    def patch(self, request, pk):
        _permission(request, PermissionCode.INVENTORY_RECIPE_MANAGE)
        serializer = RecipeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        if "inputs" in values:
            values["inputs"] = [_line_command(row) for row in values["inputs"]]
        if "outputs" in values:
            values["outputs"] = [
                _line_command(row, output=True) for row in values["outputs"]
            ]
        recipe = _run(lambda: _use_case().update(
            request.business.id, pk, **values,
        ))
        return Response(RecipeSerializer(recipe).data)


class RecipeLineCollectionAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]
    line_kind = "input"

    def post(self, request, recipe_id):
        _permission(request, PermissionCode.INVENTORY_RECIPE_MANAGE)
        line_serializer = (
            RecipeOutputWriteSerializer if self.line_kind == "output"
            else RecipeLineWriteSerializer
        )(data=request.data)
        line_serializer.is_valid(raise_exception=True)
        recipe = _run(lambda: _use_case().add_line(
            request.business.id,
            recipe_id,
            self.line_kind,
            _line_command(line_serializer.validated_data, output=self.line_kind == "output"),
        ))
        return Response(RecipeSerializer(recipe).data, status=status.HTTP_201_CREATED)


class RecipeInputCollectionAPIView(RecipeLineCollectionAPIView):
    line_kind = "input"


class RecipeOutputCollectionAPIView(RecipeLineCollectionAPIView):
    line_kind = "output"


class RecipeLineDetailAPIView(TenantAPIView):
    permission_classes = [IsAuthenticated]
    line_kind = "input"

    def patch(self, request, recipe_id, line_id):
        _permission(request, PermissionCode.INVENTORY_RECIPE_MANAGE)
        serializer = (
            RecipeOutputPatchSerializer if self.line_kind == "output"
            else RecipeInputPatchSerializer
        )(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = _run(lambda: _use_case().patch_line(
            request.business.id, recipe_id, self.line_kind, line_id,
            serializer.validated_data,
        ))
        return Response(RecipeSerializer(updated).data)

    def delete(self, request, recipe_id, line_id):
        _permission(request, PermissionCode.INVENTORY_RECIPE_MANAGE)
        _run(lambda: _use_case().delete_line(
            request.business.id, recipe_id, self.line_kind, line_id,
        ))
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeInputDetailAPIView(RecipeLineDetailAPIView):
    line_kind = "input"


class RecipeOutputDetailAPIView(RecipeLineDetailAPIView):
    line_kind = "output"
