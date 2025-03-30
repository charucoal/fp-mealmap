from .models import *
from django_countries.serializer_fields import CountryField
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

# SERIALIZERS FOR ALL MODELS FOR API

class CustomerInfoSerializer(serializers.ModelSerializer):
    country = CountryField()
    phone_number = PhoneNumberField()

    class Meta:
        model = CustomerInfo
        fields = '__all__'

class BusinessInfoSerializer(serializers.ModelSerializer):
    country = CountryField()
    phone_number = PhoneNumberField()

    class Meta:
        model = BusinessInfo
        fields = '__all__'

class CustomUserSerializer(serializers.ModelSerializer):
    customer = CustomerInfoSerializer(read_only=True)
    business = BusinessInfoSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'account_type', 'customer', 'business']

class DietaryRegSerializer(serializers.ModelSerializer):
    business = serializers.PrimaryKeyRelatedField(queryset=BusinessInfo.objects.all())

    class Meta:
        model = DietaryReg
        fields = '__all__'

class FoodLogSerializer(serializers.ModelSerializer):
    business = serializers.PrimaryKeyRelatedField(queryset=BusinessInfo.objects.all())

    class Meta:
        model = FoodLog
        fields = '__all__'

class PurchaseLogSerializer(serializers.ModelSerializer):
    item = FoodLogSerializer(read_only=True)
    customer = CustomerInfoSerializer(read_only=True)

    class Meta:
        model = PurchaseLog
        fields = '__all__'

class ReservationLogSerializer(serializers.ModelSerializer):
    item = FoodLogSerializer(read_only=True)
    customer = CustomerInfoSerializer(read_only=True)

    class Meta:
        model = ReservationLog
        fields = '__all__'
