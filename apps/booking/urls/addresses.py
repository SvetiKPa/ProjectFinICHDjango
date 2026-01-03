from rest_framework.routers import DefaultRouter, SimpleRouter
from apps.booking.views.addresses import AddressViewSet

# router = SimpleRouter()
router = DefaultRouter()
router.register('', AddressViewSet)  #viewset

urlpatterns = [

] + router.urls
