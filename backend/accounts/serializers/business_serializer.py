from rest_framework import serializers
from accounts.models import Business



class BusinessCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ["name", "number", "address"]