from rest_framework import viewsets
from .models import *
from .serializers import *

# VIEWSETS FOR API

class CustomerInfoViewSet(viewsets.ModelViewSet):
    queryset = CustomerInfo.objects.all()
    serializer_class = CustomerInfoSerializer

class BusinessInfoViewSet(viewsets.ModelViewSet):
    queryset = BusinessInfo.objects.all()
    serializer_class = BusinessInfoSerializer

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

class DietaryRegViewSet(viewsets.ModelViewSet):
    queryset = DietaryReg.objects.all()
    serializer_class = DietaryRegSerializer

class FoodLogViewSet(viewsets.ModelViewSet):
    queryset = FoodLog.objects.all()
    serializer_class = FoodLogSerializer

class PurchaseLogViewSet(viewsets.ModelViewSet):
    queryset = PurchaseLog.objects.all()
    serializer_class = PurchaseLogSerializer

class ReservationLogViewSet(viewsets.ModelViewSet):
    queryset = ReservationLog.objects.all()
    serializer_class = ReservationLogSerializer
