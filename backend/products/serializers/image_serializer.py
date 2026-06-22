from rest_framework import serializers

class ImageUploadSerializer(serializers.Serializer):
    file = serializers.ImageField()