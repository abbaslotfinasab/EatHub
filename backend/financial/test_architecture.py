import ast
from pathlib import Path

from django.test import SimpleTestCase
from rest_framework.serializers import ModelSerializer

from financial.serializers import (
    CustomerAccountSerializer,
    CustomerTransactionSerializer,
)


class FinancialPresentationBoundaryTests(SimpleTestCase):
    def test_financial_presentation_files_do_not_import_orm_models(self):
        root = Path(__file__).parent
        for filename in ("views.py", "serializers.py"):
            syntax_tree = ast.parse(
                (root / filename).read_text(encoding="utf-8")
            )
            imported_modules = {
                alias.name
                for node in ast.walk(syntax_tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
            imported_modules.update(
                node.module
                for node in ast.walk(syntax_tree)
                if isinstance(node, ast.ImportFrom) and node.module
            )
            self.assertFalse(
                any(
                    module.startswith("django.db")
                    or module.endswith(".models")
                    for module in imported_modules
                ),
                msg=f"{filename} must not import Django ORM models",
            )

    def test_wallet_read_serializers_are_not_model_serializers(self):
        self.assertFalse(
            issubclass(CustomerAccountSerializer, ModelSerializer)
        )
        self.assertFalse(
            issubclass(CustomerTransactionSerializer, ModelSerializer)
        )
