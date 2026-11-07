import os
from unittest import TestCase
from unittest.mock import patch

from EatHub.settings import _env_bool


class EnvironmentBooleanParsingTests(TestCase):
    def test_missing_value_uses_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(_env_bool("EATHUB_TEST_FLAG"))
            self.assertTrue(_env_bool("EATHUB_TEST_FLAG", default=True))

    def test_truthy_values_are_explicit(self):
        for value in ("1", "true", "TRUE", " yes ", "on"):
            with self.subTest(value=value), patch.dict(os.environ, {"EATHUB_TEST_FLAG": value}):
                self.assertTrue(_env_bool("EATHUB_TEST_FLAG"))

    def test_false_string_is_not_truthy(self):
        for value in ("0", "false", "False", "no", "off", ""):
            with self.subTest(value=value), patch.dict(os.environ, {"EATHUB_TEST_FLAG": value}):
                self.assertFalse(_env_bool("EATHUB_TEST_FLAG"))
