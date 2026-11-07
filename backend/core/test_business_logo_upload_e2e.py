import io
import shutil
import tempfile

from django.core.files.storage import default_storage
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Business, Membership, Role, User


class BusinessLogoUploadEndToEndTests(APITestCase):
    upload_url = "/api/core/upload/"
    profile_url = "/api/accounts/business/profile/"

    def setUp(self):
        self.media_dir = tempfile.mkdtemp(prefix="eathub-business-logo-e2e-")
        self.settings_override = override_settings(MEDIA_ROOT=self.media_dir)
        self.settings_override.enable()

        self.user = User.objects.create_user(
            email="business-logo-e2e@example.com",
            password="test-password",
            name="Business Logo E2E",
            number="88991",
        )
        self.business = Business.objects.create(name="Logo E2E Business")
        owner_role = Role.objects.create(
            business=self.business,
            name="Owner",
            code="OWNER",
        )
        Membership.objects.create(
            user=self.user,
            business=self.business,
            role=owner_role,
            is_active=True,
        )
        self.client.force_authenticate(self.user)

    def tearDown(self):
        self.settings_override.disable()
        shutil.rmtree(self.media_dir, ignore_errors=True)

    @staticmethod
    def valid_png():
        buffer = io.BytesIO()
        Image.new("RGB", (48, 32), color="blue").save(buffer, format="PNG")
        return SimpleUploadedFile(
            "business-logo.png",
            buffer.getvalue(),
            content_type="image/png",
        )

    def test_upload_save_reload_and_serve_user_avatar(self):
        upload_response = self.client.post(
            self.upload_url,
            {"file": self.valid_png(), "purpose": "avatar"},
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        uploaded_path = upload_response.data["path"]
        self.assertTrue(uploaded_path.startswith(f"uploads/avatars/{self.user.pk}/"))
        self.assertTrue(default_storage.exists(uploaded_path))

        update_response = self.client.patch(
            "/api/accounts/auth/me/",
            {"avatar": uploaded_path},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar.name, uploaded_path)

        profile_response = self.client.get("/api/accounts/auth/me/")
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        avatar_url = profile_response.data["avatar"]
        self.assertTrue(avatar_url)
        self.assertTrue(avatar_url.endswith(uploaded_path))

        with default_storage.open(uploaded_path, "rb") as stored_image:
            image = Image.open(stored_image)
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (48, 32))

    def test_upload_save_reload_and_serve_business_logo(self):
        # 1. Upload the image using the same multipart API used by the frontend.
        upload_response = self.client.post(
            self.upload_url,
            {"file": self.valid_png(), "purpose": "business_logo"},
            format="multipart",
        )
        self.assertEqual(upload_response.status_code, status.HTTP_201_CREATED)
        uploaded_path = upload_response.data["path"]
        self.assertTrue(
            uploaded_path.startswith(
                f"uploads/businesses/logos/{self.user.pk}/"
            )
        )
        self.assertTrue(default_storage.exists(uploaded_path))

        # 2. Persist the returned storage path on the active business.
        update_response = self.client.patch(
            self.profile_url,
            {"logo": uploaded_path},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.business.refresh_from_db()
        self.assertEqual(self.business.logo.name, uploaded_path)

        # 3. Reload the profile and ensure the API returns a usable image URL.
        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        logo_url = profile_response.data["logo"]
        self.assertTrue(logo_url)
        self.assertTrue(logo_url.endswith(uploaded_path))

        # 4. Verify the stored object is still readable and is a valid image.
        with default_storage.open(uploaded_path, "rb") as stored_image:
            image = Image.open(stored_image)
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.size, (48, 32))
