from rest_framework.routers import DefaultRouter, SimpleRouter
from apps.booking.views.bookings import BookingViewSet

# router = SimpleRouter()
router = DefaultRouter()
router.register('', BookingViewSet, basename='booking')  #viewset

urlpatterns = [

] + router.urls
