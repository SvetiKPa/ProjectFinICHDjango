from django.urls import path, include
from rest_framework.routers import DefaultRouter, SimpleRouter
from apps.booking.views.listings import ListingViewSet
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


# router = SimpleRouter()
router = DefaultRouter()
router.register('', ListingViewSet)  #viewset

urlpatterns = [


] + router.urls
