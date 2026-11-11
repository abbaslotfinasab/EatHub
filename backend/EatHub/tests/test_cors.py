from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from corsheaders.middleware import CorsMiddleware


class BusinessContextCorsTests(SimpleTestCase):
    @override_settings(CORS_ALLOWED_ORIGINS=["https://eathub.ir"])
    def test_preflight_allows_business_context_header(self):
        request = RequestFactory().options(
            "/api/accounts/auth/me/",
            HTTP_ORIGIN="https://eathub.ir",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS=(
                "authorization,content-type,x-business-id"
            ),
        )
        middleware = CorsMiddleware(lambda request: HttpResponse())

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "https://eathub.ir",
        )
        allowed_headers = response["Access-Control-Allow-Headers"].lower()
        self.assertIn("x-business-id", allowed_headers)
        self.assertIn("authorization", allowed_headers)
        self.assertIn("content-type", allowed_headers)
