from django.urls import path
from rest_framework.routers import DefaultRouter
from apps.booking.views.calendars import CalendarViewSet

router = DefaultRouter()
router.register('', CalendarViewSet)  #viewset

urlpatterns = [

] + router.urls

