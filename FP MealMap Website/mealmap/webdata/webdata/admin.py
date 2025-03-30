from django.contrib import admin
from .models import *

# register models to admin page
admin.site.register(CustomUser)
admin.site.register(BusinessInfo)
admin.site.register(CustomerInfo)
admin.site.register(FoodLog)
admin.site.register(PurchaseLog)
admin.site.register(ReservationLog)
admin.site.register(DietaryReg)