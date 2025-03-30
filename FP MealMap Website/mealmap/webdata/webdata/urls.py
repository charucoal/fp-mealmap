from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from .viewsets import *
from .views import *

router = DefaultRouter()
router.register(r'customers', CustomerInfoViewSet)
router.register(r'businesses', BusinessInfoViewSet)
router.register(r'users', CustomUserViewSet)
router.register(r'dietary', DietaryRegViewSet)
router.register(r'foodlogs', FoodLogViewSet)
router.register(r'purchases', PurchaseLogViewSet)
router.register(r'reservations', ReservationLogViewSet)

urlpatterns = [
    ######### API URL paths #########
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'), # OpenAPI JSON Schema
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), # Swagger UI
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'), # ReDoc UI

    ######### MEALMAP URL paths #########

    # LOGGED OUT URLs
    path('', index, name='landing'),
    path('home/', home, name='home'),
    path('login/', user_login, name='login'),
    path('signup/business/', register_business, name='business-signup'),
    path('signup/customer/', register_customer, name='customer-signup'),

    path('logout/', user_logout, name='logout'),

    # BUSINESS PAGES URLs
    path('business/home/', business_home, name='business-home'),
    path('business/reservation/view/', business_view_reservation, name='businses-view-reservation'),
    path('business/log/upload', business_upload_foodlog, name='business-upload-log'),
    path('business/log/upload/csv', business_upload_foodlog_csv, name='business-upload-log-csv'),
    path('business/log/upload/manual', business_upload_foodlog_manual, name='business-upload-log-manual'),
    path('business/log/review', business_review_foodlog, name='business-review-log'),
    path('business/log/alert', send_out_alerts, name='business-alert-log'),
    path('business/purchase/log', business_log_purchase, name='business-log-purchase'),
    path('business/profile/', business_profile, name='business-profile'),
    path('business/password/', business_setpassword, name='business-set-password'),
    path('business/log/view', business_view_foodlog, name='business-view-log'),
    path('business/purchase/view', business_view_purchases, name='business-view-purchase'),

    # CUSTOMER PAGES URLs
    path('customer/home/', customer_home, name='customer-home'),
    path('customer/offers/', customer_view_offers, name='customer-view-offers'),
    path('customer/reservation/view/', customer_view_reservation, name='customer-view-reservation'),
    path('customer/reservation/make/', customer_make_reservation, name='customer-make-reservation'),
    path('customer/profile/', customer_profile, name='customer-profile'),
    path('customer/password/', customer_setpassword, name='customer-set-password'),
    path('customer/history/', customer_purchase, name='customer-history'),
    path('customer/view/', customer_view_restaurant, name='restaurant-details'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
