"""Architecture guard: domain modules stay independent of frameworks and outer layers."""

import ast
from pathlib import Path
import unittest


BACKEND_ROOT = Path(__file__).resolve().parents[3]
DOMAIN_ROOTS = sorted(
    path for path in BACKEND_ROOT.glob("*/domain") if path.is_dir()
)
FORBIDDEN_ROOTS = {"django", "rest_framework"}
FORBIDDEN_LAYERS = {"presentation", "infrastructure"}


def _forbidden_imports(source: str):
    tree = ast.parse(source)
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            modules = [node.module or ""]
        else:
            continue

        for module in modules:
            parts = module.split(".") if module else []
            if parts and parts[0] in FORBIDDEN_ROOTS:
                violations.append((node.lineno, module))
            elif any(part in FORBIDDEN_LAYERS for part in parts):
                violations.append((node.lineno, module))
    return violations


class DomainImportBoundaryTests(unittest.TestCase):
    def test_domain_does_not_import_framework_or_outer_layers(self):
        self.assertTrue(DOMAIN_ROOTS, "No backend domain directories were discovered")

        violations = []
        for domain_root in DOMAIN_ROOTS:
            for source_file in sorted(domain_root.rglob("*.py")):
                # Test modules may use Django's test framework; the boundary
                # applies to production Domain code, not its test harness.
                if "tests" in source_file.relative_to(domain_root).parts:
                    continue

                try:
                    source = source_file.read_text(encoding="utf-8")
                    imports = _forbidden_imports(source)
                except SyntaxError as exc:
                    violations.append(
                        f"{source_file.relative_to(BACKEND_ROOT)}:{exc.lineno}: "
                        f"invalid Python syntax ({exc.msg})"
                    )
                    continue

                for line_number, module in imports:
                    violations.append(
                        f"{source_file.relative_to(BACKEND_ROOT)}:{line_number}: "
                        f"forbidden import '{module}'"
                    )

        self.assertFalse(
            violations,
            "Domain import boundary violations found:\n" + "\n".join(violations),
        )
