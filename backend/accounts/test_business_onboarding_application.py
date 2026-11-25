from unittest import TestCase

from accounts.application.business_onboarding import CreateBusiness
from accounts.application.business_onboarding_result import CreatedBusiness


class FakeBusinessOnboardingRepository:
    def __init__(self):
        self.calls = []
        self.result = CreatedBusiness(business_id=41, business_name="Test Cafe")

    def create_business_with_owner(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class CreateBusinessTests(TestCase):
    def test_delegates_onboarding_to_repository_and_returns_result(self):
        repository = FakeBusinessOnboardingRepository()
        use_case = CreateBusiness(repository)

        result = use_case.execute(
            user_id=7, name="Test Cafe", number="123", address="Main Street", logo="logo.png",
        )

        self.assertEqual(result, repository.result)
        self.assertEqual(repository.calls, [{
            "user_id": 7,
            "name": "Test Cafe",
            "number": "123",
            "address": "Main Street",
            "logo": "logo.png",
        }])

    def test_optional_business_fields_keep_legacy_defaults(self):
        repository = FakeBusinessOnboardingRepository()
        CreateBusiness(repository).execute(user_id=9, name="No Frills Cafe")

        self.assertEqual(repository.calls, [{
            "user_id": 9,
            "name": "No Frills Cafe",
            "number": "",
            "address": "",
            "logo": None,
        }])
