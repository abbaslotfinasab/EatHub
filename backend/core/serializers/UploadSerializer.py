from rest_framework import serializers


class UploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    purpose = serializers.ChoiceField(
        choices=("avatar", "business_logo", "generic"),
        default="generic",
    )
